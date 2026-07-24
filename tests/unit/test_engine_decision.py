from contracts.capability import CapabilityProfile, ExcelInstallation
from contracts.operation import OperationSpec, TargetSpec
from engines.router import EngineRouter

def test_com_required_fails_closed_without_excel():
    op=OperationSpec(opcode='SAVE_AS', target=TargetSpec())
    decision=EngineRouter().decide(op, CapabilityProfile(excel=ExcelInstallation(installed=False)))
    assert not decision.supported
    assert decision.engine is None
    assert 'Excel COM' in decision.reason
