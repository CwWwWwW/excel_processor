from __future__ import annotations
from uuid import UUID
from contracts.result import VerificationReport, VerificationStatus
from .file_validator import validate_file_basic
from .workbook_validator import validate_excel_com_reopen, validate_ooxml_container, validate_openxml_reopen
def build_file_report(job_id: UUID, file_id: UUID, path, excel_installed: bool=False) -> VerificationReport:
    checks,warnings,errors,digest=validate_file_basic(path); warn=list(warnings); err=list(errors)
    if digest: checks['sha256']=True
    for name, validator in [('ooxml_container', lambda: validate_ooxml_container(path)), ('openxml_reopen', lambda: validate_openxml_reopen(path)), ('excel_com_reopen', lambda: validate_excel_com_reopen(path, excel_installed))]:
        ok,msg=validator(); checks[name]=ok
        if msg and ok: warn.append(msg)
        if msg and not ok: err.append(msg)
    status=VerificationStatus.PASS if not warn and not err else VerificationStatus.PASS_WITH_WARNINGS if warn and not err else VerificationStatus.REJECTED
    return VerificationReport(job_id=job_id, file_id=file_id, status=status, checks=checks, warnings=tuple(warn), errors=tuple(err))
