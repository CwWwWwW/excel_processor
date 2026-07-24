from __future__ import annotations
from pathlib import Path
from contracts.job import EngineMode, JobSpec
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import JobResult
from compiler.plan_compiler import PlanCompiler
from discovery.excel_detector import build_capability_profile
from discovery.workbook_inspector import inspect_workbook
from engines.com import ExcelComEngine
from engines.dataframe import DataFrameEngine
from engines.hybrid import HybridEngine
from engines.openxml import OpenXmlEngine
from transaction.workspace import JobWorkspace
from validation.report_builder import build_file_report
class JobScheduler:
    def __init__(self, runtime_root: Path) -> None: self.runtime_root=runtime_root
    def run_preview(self, job: JobSpec):
        cap=build_capability_profile(); snapshots={f.file_id: inspect_workbook(f.file_id, f.source_path).stable_hash() for f in job.files}
        return PlanCompiler().compile(job, cap, snapshots)
    def run(self, job: JobSpec) -> JobResult:
        cap=build_capability_profile(); ws=JobWorkspace(self.runtime_root, job.job_id); plan=self.run_preview(job); ctx=ExecutionContext(job_id=job.job_id, runtime_root=self.runtime_root, capability=cap.model_dump(mode="json")); warnings=list(plan.warnings); errors=[]
        engines={EngineMode.EXCEL_COM:ExcelComEngine(), EngineMode.OPENXML:OpenXmlEngine(), EngineMode.DATAFRAME:DataFrameEngine(), EngineMode.HYBRID:HybridEngine()}
        for f in job.files:
            working=ws.prepare_file(f)
            for planned in plan.operations:
                if f.file_id not in planned.resolved_file_ids: continue
                cmd=OperationCommand(job_id=job.job_id, operation=planned.command, file_id=f.file_id, working_path=working, selected_engine=planned.selected_engine, resolved_sheet=(planned.resolved_sheets[0] if planned.resolved_sheets else None))
                res=engines[planned.selected_engine].execute(cmd, ctx); warnings.extend(res.warnings); errors.extend(res.errors)
                if not res.success: return JobResult(job_id=job.job_id, success=False, warnings=tuple(warnings), errors=tuple(errors))
            report=build_file_report(job.job_id, f.file_id, working); warnings.extend(report.warnings); errors.extend(report.errors)
        return JobResult(job_id=job.job_id, success=not errors, warnings=tuple(warnings), errors=tuple(errors))
