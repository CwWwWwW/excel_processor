import pytest
from contracts.state import JobState, assert_transition

def test_running_cannot_commit_directly():
    with pytest.raises(ValueError): assert_transition(JobState.RUNNING, JobState.COMMITTED)

def test_verifying_can_commit():
    assert_transition(JobState.VERIFYING, JobState.COMMITTED)
