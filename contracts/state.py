from __future__ import annotations
from enum import StrEnum
class JobState(StrEnum):
    CREATED="CREATED"; ENVIRONMENT_SCANNED="ENVIRONMENT_SCANNED"; FILES_DISCOVERED="FILES_DISCOVERED"; RULES_COMPILED="RULES_COMPILED"; PLAN_VALIDATED="PLAN_VALIDATED"; PREVIEWED="PREVIEWED"; RUNNING="RUNNING"; SAVING_TEMP="SAVING_TEMP"; VERIFYING="VERIFYING"; COMMITTED="COMMITTED"; PAUSED="PAUSED"; CANCELLING="CANCELLING"; FAILED="FAILED"; REJECTED="REJECTED"; ROLLED_BACK="ROLLED_BACK"
_ALLOWED = {
    JobState.CREATED:{JobState.ENVIRONMENT_SCANNED,JobState.FAILED},
    JobState.ENVIRONMENT_SCANNED:{JobState.FILES_DISCOVERED,JobState.FAILED},
    JobState.FILES_DISCOVERED:{JobState.RULES_COMPILED,JobState.FAILED},
    JobState.RULES_COMPILED:{JobState.PLAN_VALIDATED,JobState.FAILED},
    JobState.PLAN_VALIDATED:{JobState.PREVIEWED,JobState.FAILED},
    JobState.PREVIEWED:{JobState.RUNNING,JobState.FAILED},
    JobState.RUNNING:{JobState.PAUSED,JobState.CANCELLING,JobState.FAILED,JobState.SAVING_TEMP},
    JobState.PAUSED:{JobState.RUNNING,JobState.CANCELLING,JobState.FAILED},
    JobState.CANCELLING:{JobState.ROLLED_BACK}, JobState.FAILED:{JobState.ROLLED_BACK},
    JobState.SAVING_TEMP:{JobState.VERIFYING,JobState.FAILED},
    JobState.VERIFYING:{JobState.COMMITTED,JobState.REJECTED,JobState.FAILED},
    JobState.REJECTED:{JobState.ROLLED_BACK}, JobState.COMMITTED:set(), JobState.ROLLED_BACK:set(),
}
def assert_transition(current: JobState, next_state: JobState) -> None:
    if next_state not in _ALLOWED.get(current, set()):
        raise ValueError(f"非法任务状态转换：{current} -> {next_state}")
