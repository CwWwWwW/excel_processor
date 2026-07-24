from contracts.errors import ErrorDecider, ErrorRecord
from contracts.job import ErrorPolicy

def test_error_policy_skip_file():
    d=ErrorDecider().decide(ErrorPolicy.SKIP_FILE, ErrorRecord(code='x', message='m'))
    assert d.should_continue_job
    assert not d.should_continue_file

def test_error_policy_stop_job():
    d=ErrorDecider().decide(ErrorPolicy.STOP_JOB, ErrorRecord(code='x', message='m'))
    assert not d.should_continue_job
