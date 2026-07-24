from __future__ import annotations
import shutil
from pathlib import Path
from string import Template
from uuid import UUID
from contracts.errors import ErrorDecider, ErrorRecord
from contracts.job import EngineMode, ErrorPolicy, FileSpec, JobSpec
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import CandidateArtifact, JobResult, TransactionRecord, VerificationStatus
from contracts.state import JobState
from compiler.plan_compiler import PlanCompiler
from discovery.excel_detector import build_capability_profile
from discovery.file_scanner import sha256_file
from discovery.workbook_inspector import inspect_workbook
from engines.com import ExcelComEngine
from engines.dataframe import DataFrameEngine
from engines.hybrid import HybridEngine
from engines.openxml import OpenXmlEngine
from storage.database import Database
from storage.repositories import JobRepository
from transaction.commit import atomic_commit
from transaction.rollback import reject_candidate
from transaction.workspace import JobWorkspace
from validation.report_builder import build_file_report
class JobScheduler:
    def __init__(self, runtime_root: Path, database: Database | None=None) -> None:
        self.runtime_root=runtime_root; self.database=database or Database(runtime_root/'database'/'excel_processor.db'); self.repo=JobRepository(self.database); self.decider=ErrorDecider()
    def run_preview(self, job: JobSpec):
        cap=build_capability_profile(); snapshots={f.file_id: inspect_workbook(f.file_id, f.source_path).stable_hash() for f in job.files}
        return PlanCompiler().compile(job, cap, snapshots)
    def _state(self, job: JobSpec, state: JobState, **fields) -> None:
        try: self.repo.update_state(str(job.job_id), state, **fields)
        except Exception as exc:
            _ = exc
    def _record_error(self, record: ErrorRecord) -> None:
        try: self.repo.record_error(record)
        except Exception as exc:
            _ = exc
    def _record_tx(self, record: TransactionRecord) -> None:
        try: self.repo.record_transaction(record)
        except Exception as exc:
            _ = exc
    def _output_path(self, job: JobSpec, file_spec: FileSpec) -> Path:
        source=file_spec.source_path.resolve(); stem=Template(job.output.filename_template).safe_substitute(file_stem=source.stem, file_name=source.name, file_ext=source.suffix.lstrip('.'))
        suffix = source.suffix if job.output.preserve_source_format or job.output.format_code is None else source.suffix
        target=(job.output.output_directory / f'{stem}{suffix}').resolve()
        if target == source: raise ValueError('???????????????')
        return target
    def _sheets_for(self, planned, snapshot) -> tuple[str | None, ...]:
        if planned.resolved_sheets: return tuple(planned.resolved_sheets)
        names = tuple(snapshot.sheets) if snapshot and snapshot.sheets else ()
        return names or (None,)
    def _engines(self):
        return {EngineMode.EXCEL_COM:ExcelComEngine(), EngineMode.OPENXML:OpenXmlEngine(), EngineMode.DATAFRAME:DataFrameEngine(), EngineMode.HYBRID:HybridEngine()}
    def run(self, job: JobSpec) -> JobResult:
        cap=build_capability_profile(); workspace=JobWorkspace(self.runtime_root, job.job_id); warnings=[]; errors=[]; artifacts=[]; reports=[]
        self.repo.save_job(job, JobState.CREATED, workspace_path=str(workspace.root)); self._state(job, JobState.PREPARED, workspace_path=workspace.root)
        plan=self.run_preview(job); ctx=ExecutionContext(job_id=job.job_id, runtime_root=self.runtime_root, capability=cap.model_dump(mode='json')); engines=self._engines(); self._state(job, JobState.RUNNING)
        try:
            for file_spec in job.files:
                file_failed=False; working=workspace.prepare_file(file_spec); snapshot=inspect_workbook(file_spec.file_id, file_spec.source_path)
                self._record_tx(TransactionRecord(job_id=job.job_id, file_id=file_spec.file_id, stage='working_prepared', path=working, sha256=sha256_file(working)))
                for planned in plan.operations:
                    if file_failed or file_spec.file_id not in planned.resolved_file_ids: continue
                    if planned.engine_decision and not planned.engine_decision.supported:
                        record=ErrorRecord(job_id=job.job_id, file_id=file_spec.file_id, operation_id=planned.command.operation_id, code='ENGINE_UNSUPPORTED', message=planned.engine_decision.reason)
                        self._record_error(record); errors.append(record.message); decision=self.decider.decide(planned.command.error_policy, record)
                        if not decision.should_continue_job: raise RuntimeError(record.message)
                        if not decision.should_continue_file: file_failed=True
                        continue
                    engine=planned.selected_engine
                    if engine is None:
                        record=ErrorRecord(job_id=job.job_id, file_id=file_spec.file_id, operation_id=planned.command.operation_id, code='ENGINE_NONE', message='??????????')
                        self._record_error(record); errors.append(record.message); raise RuntimeError(record.message)
                    sheet_failed=set()
                    for sheet in self._sheets_for(planned, snapshot):
                        if sheet in sheet_failed: continue
                        cmd=OperationCommand(job_id=job.job_id, operation=planned.command, file_id=file_spec.file_id, working_path=working, selected_engine=engine, resolved_sheet=sheet)
                        result=engines[engine].execute(cmd, ctx); self.repo.record_operation_result(str(job.job_id), result); warnings.extend(result.warnings); errors.extend(result.errors)
                        if not result.success:
                            record=ErrorRecord(job_id=job.job_id, file_id=file_spec.file_id, operation_id=planned.command.operation_id, sheet_name=sheet, code='OPERATION_FAILED', message='; '.join(result.errors) or '????')
                            self._record_error(record); decision=self.decider.decide(planned.command.error_policy, record)
                            if not decision.should_continue_job: raise RuntimeError(record.message)
                            if not decision.should_continue_file: file_failed=True; break
                            if not decision.should_continue_sheet: sheet_failed.add(sheet); continue
                            if not decision.should_continue_operation: break
                if file_failed: continue
                candidate=workspace.candidate_path_for(file_spec.source_path); shutil.copy2(working, candidate); self._state(job, JobState.CANDIDATE_SAVED)
                digest=sha256_file(candidate); artifact=CandidateArtifact(job_id=job.job_id, file_id=file_spec.file_id, candidate_path=candidate, sha256=digest, size_bytes=candidate.stat().st_size); artifacts.append(artifact)
                self._record_tx(TransactionRecord(job_id=job.job_id, file_id=file_spec.file_id, stage='candidate_saved', path=candidate, sha256=digest))
                self._state(job, JobState.VERIFYING); report=build_file_report(job.job_id, file_spec.file_id, candidate, excel_installed=cap.excel.installed); reports.append(report); self.repo.record_verification_report(report); warnings.extend(report.warnings); errors.extend(report.errors)
                if report.status == VerificationStatus.REJECTED or (report.status == VerificationStatus.PASS_WITH_WARNINGS and not job.output.allow_warnings):
                    reject_candidate(candidate, workspace.rejected); self._state(job, JobState.REJECTED); raise RuntimeError('??????????????')
                if not job.preview_only:
                    committed=workspace.committed_path_for(file_spec.source_path); shutil.copy2(candidate, committed)
                    final=atomic_commit(committed, self._output_path(job, file_spec), overwrite_policy=job.output.overwrite_policy, backup_dir=workspace.backup)
                    self._record_tx(TransactionRecord(job_id=job.job_id, file_id=file_spec.file_id, stage='committed', path=final, sha256=sha256_file(final)))
            self._state(job, JobState.COMMITTED); workspace.cleanup_temp(); self._state(job, JobState.CLEANED)
            return JobResult(job_id=job.job_id, success=not errors, artifacts=tuple(artifacts), reports=tuple(reports), warnings=tuple(warnings), errors=tuple(errors))
        except Exception as exc:
            record=ErrorRecord(job_id=job.job_id, code='JOB_FAILED', message=str(exc)); self._record_error(record); errors.append(str(exc)); self._state(job, JobState.REJECTED)
            self._state(job, JobState.ROLLED_BACK); workspace.cleanup_temp(); self._state(job, JobState.CLEANED)
            return JobResult(job_id=job.job_id, success=False, artifacts=tuple(artifacts), reports=tuple(reports), warnings=tuple(warnings), errors=tuple(errors))
