import pytest
from contracts.operation import OperationSpec, TargetSpec
from operations.generic_com.executor import execute_generic_com

def test_generic_com_blocks_run():
    with pytest.raises(ValueError):
        execute_generic_com(object(), OperationSpec(opcode='COM_CALL', target=TargetSpec(), parameters={'member':'Run'}), allowed_members={'Run'})
