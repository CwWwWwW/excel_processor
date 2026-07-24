from __future__ import annotations
from uuid import UUID
from contracts.result import VerificationReport, VerificationStatus
from .file_validator import validate_file_basic
from .workbook_validator import validate_openxml_reopen
def build_file_report(job_id: UUID, file_id: UUID, path) -> VerificationReport:
    checks,warnings,errors=validate_file_basic(path); reopen_ok,reopen_msg=validate_openxml_reopen(path); checks["reopen"]=reopen_ok; warn=list(warnings); err=list(errors)
    if reopen_msg and reopen_ok: warn.append(reopen_msg)
    if reopen_msg and not reopen_ok: err.append(reopen_msg)
    status=VerificationStatus.PASS if not warn and not err else VerificationStatus.PASS_WITH_WARNINGS if warn and not err else VerificationStatus.REJECTED
    return VerificationReport(job_id=job_id, file_id=file_id, status=status, checks=checks, warnings=tuple(warn), errors=tuple(err))
