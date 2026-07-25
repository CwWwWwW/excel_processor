from __future__ import annotations
import shutil
from dataclasses import dataclass
from pathlib import Path
from string import Template

from contracts.errors import ErrorDecider, ErrorRecord, FileExecutionState
from contracts.job import AtomicityMode, EngineMode, ErrorPolicy, FileSpec, JobSpec
from contracts.operation import OperationSpec, TargetSpec
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import CandidateArtifact, JobResult, TransactionRecord, VerificationStatus
from contracts.state import JobState
from compiler.plan_compiler import PlanCompiler
from discovery.excel_detector import build_capability_profile
from discovery.file_scanner import sha256_file
from discovery.workbook_inspector import inspect_workbook
from engines.dataframe import DataFrameEngine
from engines.hybrid import HybridEngine
from engines.openxml import OpenXmlEngine
from operations import build_default_registry
from output.output_planner import OutputConversionPlan, plan_output_conversion
from scheduler.worker_process import ExcelWorkerPool
from storage.database import Database
from storage.repositories import JobRepository
from transaction.commit import atomic_commit
from transaction.rollback import reject_candidate
from transaction.workspace import JobWorkspace
from validation.report_builder import build_file_report


@dataclass
class _FileRun:
    file_spec: FileSpec
    working: Path
    snapshot: object
    state: FileExecutionState
    candidate: Path | None = None
    output_plan: OutputConversionPlan | None = None
    final_path: Path | None = None
    output_backup: Path | None = None
    committed_path: Path | None = None
    failed: bool = False


class JobScheduler:
    def __init__(self, runtime_root: Path, database: Database | None = None, worker_pool: ExcelWorkerPool | None = None) -> None:
        self.runtime_root = runtime_root
        self.database = database or Database(runtime_root / "database" / "excel_processor.db")
        self.repo = JobRepository(self.database)
        self.decider = ErrorDecider()
        self.registry = build_default_registry()
        self.worker_pool = worker_pool or ExcelWorkerPool()

    def run_preview(self, job: JobSpec):
        cap = build_capability_profile()
        snapshots = {f.file_id: inspect_workbook(f.file_id, f.source_path) for f in job.files}
        return PlanCompiler().compile(job, cap, snapshots)

    def _state(self, job: JobSpec, state: JobState, **fields) -> None:
        try:
            self.repo.update_state(str(job.job_id), state, **fields)
        except Exception as exc:
            _ = exc

    def _record_error(self, record: ErrorRecord) -> None:
        try:
            self.repo.record_error(record)
        except Exception as exc:
            _ = exc

    def _record_tx(self, record: TransactionRecord) -> None:
        try:
            self.repo.record_transaction(record)
        except Exception as exc:
            _ = exc

    def _output_path(self, job: JobSpec, file_spec: FileSpec, plan: OutputConversionPlan | None = None) -> Path:
        source = file_spec.source_path.resolve()
        stem = Template(job.output.filename_template).safe_substitute(file_stem=source.stem, file_name=source.name, file_ext=source.suffix.lstrip("."))
        suffix = source.suffix if plan is None else plan.target_extension
        target = (job.output.output_directory / f"{stem}{suffix}").resolve()
        if target == source:
            raise ValueError("Output path cannot be the source path")
        return target

    def _sheets_for(self, planned, snapshot) -> tuple[str | None, ...]:
        if planned.resolved_sheets:
            return tuple(planned.resolved_sheets)
        names = tuple(getattr(snapshot, "sheets", ())) if snapshot and getattr(snapshot, "sheets", None) else ()
        return names or (None,)

    def _local_engines(self):
        return {EngineMode.OPENXML: OpenXmlEngine(), EngineMode.DATAFRAME: DataFrameEngine(), EngineMode.HYBRID: HybridEngine()}

    def _execute_command(self, command: OperationCommand, ctx: ExecutionContext, cap, snapshot) -> object:
        handler = self.registry.get(command.operation.opcode)
        validation_errors = handler.validate(command, cap, snapshot)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        if command.selected_engine == EngineMode.EXCEL_COM:
            return self.worker_pool.execute(command, ctx)
        return handler.execute(command, ctx)

    def _handle_failure(self, state: FileExecutionState, job: JobSpec, policy: ErrorPolicy, record: ErrorRecord) -> tuple[bool, bool]:
        self._record_error(record)
        decision = self.decider.apply(state, policy, record)
        stop_job = not decision.should_continue_job
        stop_file = not decision.should_continue_file
        return stop_job, stop_file

    def _prepare_runs(self, job: JobSpec, workspace: JobWorkspace) -> list[_FileRun]:
        runs = []
        for file_spec in job.files:
            working = workspace.prepare_file(file_spec)
            snapshot = inspect_workbook(file_spec.file_id, file_spec.source_path)
            self._record_tx(TransactionRecord(job_id=job.job_id, file_id=file_spec.file_id, atomicity_mode=job.atomicity_mode, source_path=file_spec.source_path, working_path=working, source_sha256=sha256_file(file_spec.source_path), state="working_prepared", stage="working_prepared", path=working, sha256=sha256_file(working)))
            runs.append(_FileRun(file_spec=file_spec, working=working, snapshot=snapshot, state=FileExecutionState(file_id=file_spec.file_id)))
        return runs

    def _run_operations(self, job: JobSpec, plan, runs: list[_FileRun], ctx: ExecutionContext, cap, warnings: list[str], errors: list[str]) -> bool:
        local_engines = self._local_engines()
        by_file = {run.file_spec.file_id: run for run in runs}
        for planned in plan.operations:
            for file_id in planned.resolved_file_ids:
                run = by_file[file_id]
                if run.failed or planned.command.operation_id in run.state.skipped_operations:
                    continue
                if planned.engine_decision and not planned.engine_decision.supported:
                    record = ErrorRecord(job_id=job.job_id, file_id=file_id, operation_id=planned.command.operation_id, code="ENGINE_UNSUPPORTED", message=planned.engine_decision.reason)
                    errors.append(record.message)
                    stop_job, stop_file = self._handle_failure(run.state, job, planned.command.error_policy, record)
                    run.failed = run.failed or stop_file
                    if stop_job:
                        return False
                    continue
                engine = planned.selected_engine
                if engine is None:
                    record = ErrorRecord(job_id=job.job_id, file_id=file_id, operation_id=planned.command.operation_id, code="ENGINE_NONE", message="No engine selected")
                    errors.append(record.message)
                    stop_job, stop_file = self._handle_failure(run.state, job, planned.command.error_policy, record)
                    run.failed = run.failed or stop_file
                    if stop_job:
                        return False
                    continue
                for sheet in self._sheets_for(planned, run.snapshot):
                    if sheet and sheet in run.state.skipped_sheets:
                        continue
                    command = OperationCommand(job_id=job.job_id, operation=planned.command, file_id=file_id, working_path=run.working, selected_engine=engine, resolved_sheet=sheet)
                    try:
                        result = self._execute_command(command, ctx, cap, run.snapshot)
                    except Exception as exc:
                        result = None
                        record = ErrorRecord(job_id=job.job_id, file_id=file_id, operation_id=planned.command.operation_id, sheet_name=sheet, code="OPERATION_FAILED", message=str(exc))
                        errors.append(record.message)
                        stop_job, stop_file = self._handle_failure(run.state, job, planned.command.error_policy, record)
                        run.failed = run.failed or stop_file or planned.command.error_policy == ErrorPolicy.STOP_JOB
                        if stop_job:
                            return False
                        if stop_file:
                            break
                        continue
                    self.repo.record_operation_result(str(job.job_id), result)
                    warnings.extend(result.warnings)
                    if not result.success:
                        record = ErrorRecord(job_id=job.job_id, file_id=file_id, operation_id=planned.command.operation_id, sheet_name=sheet, code="OPERATION_FAILED", message="; ".join(result.errors) or "Operation failed")
                        if planned.command.error_policy == ErrorPolicy.CONTINUE:
                            warnings.append(record.message)
                        else:
                            errors.append(record.message)
                        stop_job, stop_file = self._handle_failure(run.state, job, planned.command.error_policy, record)
                        if planned.command.error_policy == ErrorPolicy.SKIP_SHEET and sheet:
                            run.state.skipped_sheets.add(sheet)
                            break
                        if planned.command.error_policy == ErrorPolicy.SKIP_OPERATION:
                            run.state.skipped_operations.add(planned.command.operation_id)
                            break
                        run.failed = run.failed or stop_file
                        if stop_job:
                            return False
                        if stop_file:
                            break
        return True

    def _save_candidate(self, job: JobSpec, workspace: JobWorkspace, run: _FileRun, ctx: ExecutionContext, cap, warnings: list[str]) -> CandidateArtifact:
        plan = plan_output_conversion(run.snapshot, job.output, cap, job.output.compatibility_baseline)
        suffix_source = run.file_spec.source_path.with_suffix(plan.target_extension)
        candidate = workspace.candidate_path_for(suffix_source)
        run.output_plan = plan
        run.candidate = candidate
        if plan.export_mode == "copy_working_to_candidate":
            shutil.copy2(run.working, candidate)
        else:
            opcode = "EXPORT_PDF" if plan.target_extension == ".pdf" else "EXPORT_XPS" if plan.target_extension == ".xps" else "SAVE_AS"
            sheet_names = tuple(getattr(run.snapshot, "sheets", ())[:1]) or None
            op = OperationSpec(opcode=opcode, target=TargetSpec(sheet_names=sheet_names), parameters={"file_format": plan.excel_file_format} if plan.excel_file_format is not None else {})
            command = OperationCommand(job_id=job.job_id, operation=op, file_id=run.file_spec.file_id, working_path=run.working, output_path=candidate, selected_engine=EngineMode.EXCEL_COM, resolved_sheet=None)
            result = self.worker_pool.execute(command, ctx)
            self.repo.record_operation_result(str(job.job_id), result)
            warnings.extend(result.warnings)
            if not result.success:
                raise RuntimeError("; ".join(result.errors) or f"Output conversion failed for {run.file_spec.source_path}")
        self._state(job, JobState.CANDIDATE_SAVED)
        digest = sha256_file(candidate)
        artifact = CandidateArtifact(job_id=job.job_id, file_id=run.file_spec.file_id, candidate_path=candidate, sha256=digest, size_bytes=candidate.stat().st_size)
        self._record_tx(TransactionRecord(job_id=job.job_id, file_id=run.file_spec.file_id, atomicity_mode=job.atomicity_mode, source_path=run.file_spec.source_path, working_path=run.working, candidate_path=candidate, source_sha256=sha256_file(run.file_spec.source_path), candidate_sha256=digest, state="candidate_saved", stage="candidate_saved", path=candidate, sha256=digest))
        return artifact

    def _verify_candidate(self, job: JobSpec, run: _FileRun, cap, reports: list, warnings: list[str], errors: list[str]) -> bool:
        assert run.candidate is not None
        self._state(job, JobState.VERIFYING)
        report = build_file_report(job.job_id, run.file_spec.file_id, run.candidate, excel_installed=cap.excel.installed)
        reports.append(report)
        self.repo.record_verification_report(report)
        warnings.extend(report.warnings)
        errors.extend(report.errors)
        return not (report.status == VerificationStatus.REJECTED or (report.status == VerificationStatus.PASS_WITH_WARNINGS and not job.output.allow_warnings))

    def _backup_output(self, workspace: JobWorkspace, target: Path) -> Path | None:
        if not target.exists():
            return None
        backup_dir = workspace.backup / "original_outputs"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{target.name}.{sha256_file(target)[:12]}.bak"
        shutil.copy2(target, backup)
        return backup

    def _restore_commits(self, runs: list[_FileRun]) -> None:
        for run in reversed(runs):
            if run.final_path is None or run.committed_path is None:
                continue
            if run.output_backup and run.output_backup.exists():
                shutil.copy2(run.output_backup, run.final_path)
            elif run.final_path.exists():
                run.final_path.unlink()

    def _commit_run(self, job: JobSpec, workspace: JobWorkspace, run: _FileRun) -> None:
        assert run.candidate is not None
        final = self._output_path(job, run.file_spec, run.output_plan)
        run.final_path = final
        run.output_backup = self._backup_output(workspace, final)
        committed = workspace.committed_path_for(final)
        shutil.copy2(run.candidate, committed)
        target = atomic_commit(committed, final, overwrite_policy=job.output.overwrite_policy, backup_dir=workspace.backup)
        run.committed_path = target
        self._record_tx(TransactionRecord(job_id=job.job_id, file_id=run.file_spec.file_id, atomicity_mode=job.atomicity_mode, source_path=run.file_spec.source_path, working_path=run.working, candidate_path=run.candidate, committed_path=target, original_output_backup=run.output_backup, source_sha256=sha256_file(run.file_spec.source_path), candidate_sha256=sha256_file(run.candidate), committed_sha256=sha256_file(target), state="committed", stage="committed", path=target, sha256=sha256_file(target)))

    def run(self, job: JobSpec) -> JobResult:
        cap = build_capability_profile()
        workspace = JobWorkspace(self.runtime_root, job.job_id)
        warnings: list[str] = []
        errors: list[str] = []
        artifacts: list[CandidateArtifact] = []
        reports = []
        status = "FAILED"
        self.repo.save_job(job, JobState.CREATED, workspace_path=str(workspace.root))
        self._state(job, JobState.PREPARED, workspace_path=workspace.root)
        snapshots = {f.file_id: inspect_workbook(f.file_id, f.source_path) for f in job.files}
        plan = PlanCompiler().compile(job, cap, snapshots)
        ctx = ExecutionContext(job_id=job.job_id, runtime_root=self.runtime_root, capability=cap.model_dump(mode="json"))
        self._state(job, JobState.RUNNING)
        runs: list[_FileRun] = []
        try:
            runs = self._prepare_runs(job, workspace)
            operations_ok = self._run_operations(job, plan, runs, ctx, cap, warnings, errors)
            if not operations_ok and job.atomicity_mode == AtomicityMode.JOB:
                raise RuntimeError("Job stopped by error policy")
            if job.atomicity_mode == AtomicityMode.JOB and any(run.failed for run in runs):
                raise RuntimeError("One or more files failed in JOB atomicity mode")

            successful_runs: list[_FileRun] = []
            for run in runs:
                if run.failed:
                    continue
                artifact = self._save_candidate(job, workspace, run, ctx, cap, warnings)
                artifacts.append(artifact)
                if not self._verify_candidate(job, run, cap, reports, warnings, errors):
                    reject_candidate(run.candidate, workspace.rejected)
                    run.failed = True
                    if job.atomicity_mode == AtomicityMode.JOB:
                        raise RuntimeError("Candidate verification failed")
                    continue
                successful_runs.append(run)

            if not job.preview_only:
                committed: list[_FileRun] = []
                try:
                    for run in successful_runs:
                        self._commit_run(job, workspace, run)
                        committed.append(run)
                except Exception:
                    self._restore_commits(committed)
                    if job.atomicity_mode == AtomicityMode.JOB:
                        for run in successful_runs:
                            if run.candidate:
                                reject_candidate(run.candidate, workspace.rejected)
                        self._state(job, JobState.ROLLED_BACK)
                    raise

            failed_count = sum(1 for run in runs if run.failed)
            success_count = len(runs) - failed_count
            if failed_count and success_count and job.atomicity_mode == AtomicityMode.FILE:
                status = "PARTIAL_SUCCESS"
            elif errors or any(run.state.handled_errors for run in runs):
                status = "SUCCESS_WITH_WARNINGS" if success_count else "FAILED"
            else:
                status = "SUCCESS"
            self._state(job, JobState.COMMITTED)
            workspace.cleanup_temp()
            self._state(job, JobState.CLEANED)
            return JobResult(job_id=job.job_id, success=status in {"SUCCESS", "SUCCESS_WITH_WARNINGS", "PARTIAL_SUCCESS"}, status=status, artifacts=tuple(artifacts), reports=tuple(reports), warnings=tuple(warnings), errors=tuple(errors))
        except Exception as exc:
            record = ErrorRecord(job_id=job.job_id, code="JOB_FAILED", message=str(exc))
            self._record_error(record)
            errors.append(str(exc))
            for run in runs:
                if run.candidate and run.candidate.exists():
                    reject_candidate(run.candidate, workspace.rejected)
            self._restore_commits(runs)
            self._state(job, JobState.REJECTED)
            self._state(job, JobState.ROLLED_BACK)
            workspace.cleanup_temp()
            self._state(job, JobState.CLEANED)
            return JobResult(job_id=job.job_id, success=False, status="ROLLED_BACK", artifacts=tuple(artifacts), reports=tuple(reports), warnings=tuple(warnings), errors=tuple(errors))
        finally:
            try:
                self.worker_pool.shutdown()
            except Exception as shutdown_exc:
                _ = shutdown_exc
