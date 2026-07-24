from __future__ import annotations
from contracts.job import JobSpec
def parse_job_json(payload: str) -> JobSpec: return JobSpec.model_validate_json(payload)
