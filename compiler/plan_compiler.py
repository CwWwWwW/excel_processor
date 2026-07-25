from __future__ import annotations
import hashlib
from typing import Any
from contracts.capability import CapabilityProfile
from contracts.job import JobSpec
from contracts.plan import ExecutionPlan, PlannedOperation
from engines.router import EngineRouter
from .conflict_detector import detect_conflicts
from .dependency_builder import topological_sort
from .target_resolver import resolve_files


class PlanCompiler:
    def __init__(self, router: EngineRouter | None = None) -> None:
        self.router = router or EngineRouter()

    def compile(self, job: JobSpec, capability: CapabilityProfile, workbook_snapshot_hashes: dict) -> ExecutionPlan:
        ordered = topological_sort(job.operations)
        planned = []
        warnings: list[str] = []
        snapshots: dict[Any, Any] = workbook_snapshot_hashes or {}
        snapshot_hashes = {k: (v.stable_hash() if hasattr(v, "stable_hash") else str(v)) for k, v in snapshots.items()}
        for op in ordered:
            files = resolve_files(op.target, job.files)
            first_snapshot = snapshots.get(files[0].file_id) if files else None
            decision = self.router.decide(op, capability, first_snapshot if hasattr(first_snapshot, "source_path") else None)
            if not decision.supported:
                warnings.append(decision.reason)
            planned.append(
                PlannedOperation(
                    command=op,
                    resolved_file_ids=tuple(f.file_id for f in files),
                    resolved_sheets=op.target.sheet_names or (),
                    selected_engine=decision.engine,
                    engine_decision=decision,
                    dependency_ids=op.depends_on,
                    estimated_changes=max(1, len(files)),
                )
            )
        cap_hash = hashlib.sha256(capability.capability_hash_source().encode("utf-8")).hexdigest()
        return ExecutionPlan(job_id=job.job_id, capability_hash=cap_hash, workbook_snapshot_hashes=snapshot_hashes, operations=tuple(planned), warnings=tuple(warnings) + detect_conflicts(ordered))
