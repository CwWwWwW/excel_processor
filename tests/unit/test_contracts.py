from pathlib import Path
from contracts import Envelope, FileSpec, JobSpec, OperationSpec, OutputSpec, TargetSpec

def test_contracts_roundtrip_and_password_redaction():
    file_spec = FileSpec(source_path=Path('input.xlsx'), expected_password='secret')
    op = OperationSpec(opcode='SET_VALUE', target=TargetSpec(address='A1'), parameters={'value': 'x'})
    job = JobSpec(name='demo', files=(file_spec,), operations=(op,), output=OutputSpec(output_directory=Path('out')))
    payload = job.model_dump_json()
    assert 'secret' not in payload
    restored = JobSpec.model_validate_json(payload)
    env = Envelope[JobSpec](job_id=job.job_id, producer='test', payload=restored)
    assert Envelope[JobSpec].model_validate_json(env.model_dump_json()).payload.name == 'demo'
