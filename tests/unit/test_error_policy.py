from contracts.errors import ErrorDecider, ErrorRecord
from contracts.errors import FileExecutionState
from contracts.job import ErrorPolicy
from uuid import uuid4

def test_error_policy_skip_file():
    d=ErrorDecider().decide(ErrorPolicy.SKIP_FILE, ErrorRecord(code='x', message='m'))
    assert d.should_continue_job
    assert not d.should_continue_file

def test_error_policy_stop_job():
    d=ErrorDecider().decide(ErrorPolicy.STOP_JOB, ErrorRecord(code='x', message='m'))
    assert not d.should_continue_job


def test_error_policy_apply_skip_sheet_and_continue():
    file_id = uuid4()
    op_id = uuid4()
    state = FileExecutionState(file_id=file_id)
    decider = ErrorDecider()
    decider.apply(state, ErrorPolicy.SKIP_SHEET, ErrorRecord(file_id=file_id, operation_id=op_id, sheet_name="Data", code="x", message="m"))
    decider.apply(state, ErrorPolicy.CONTINUE, ErrorRecord(file_id=file_id, operation_id=op_id, code="warn", message="handled"))
    assert "Data" in state.skipped_sheets
    assert len(state.handled_errors) == 1
    assert len(state.fatal_errors) == 1
