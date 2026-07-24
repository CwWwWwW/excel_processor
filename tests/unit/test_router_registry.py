import pytest
from contracts.capability import CapabilityProfile
from contracts.job import EngineMode
from contracts.operation import OperationSpec, TargetSpec
from engines.router import EngineRouter
from operations import build_default_registry

def test_router_dataframe():
    op = OperationSpec(opcode='JOIN_TABLES', target=TargetSpec())
    assert EngineRouter().choose(op, CapabilityProfile()) == EngineMode.DATAFRAME

def test_registry_duplicate_and_missing():
    registry = build_default_registry()
    assert 'SET_VALUE' in registry.list_opcodes()
    handler = registry.get('SET_VALUE')
    with pytest.raises(ValueError): registry.register(handler)
    with pytest.raises(ValueError): registry.get('NO_SUCH_OPCODE')
