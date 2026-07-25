from pathlib import Path
from uuid import uuid4

from contracts.job import EngineMode
from contracts.operation import OperationSpec, TargetSpec
from contracts.plan import ExecutionContext, OperationCommand
from contracts.worker import WorkerRequest, WorkerResponse


def test_worker_request_response_roundtrip():
    job_id = uuid4()
    req = WorkerRequest(job_id=job_id, command="heartbeat")
    restored = WorkerRequest.model_validate_json(req.model_dump_json())
    assert restored.protocol_version == req.protocol_version
    assert restored.command == "heartbeat"
    resp = WorkerResponse(request_message_id=req.message_id, job_id=job_id, command=req.command, success=True, payload={"type": "worker_status"})
    assert WorkerResponse.model_validate_json(resp.model_dump_json()).payload["type"] == "worker_status"


def test_operation_command_serializes_for_worker():
    job_id = uuid4()
    file_id = uuid4()
    op = OperationSpec(opcode="SET_VALUE", target=TargetSpec(address="A1"), parameters={"value": "x"})
    cmd = OperationCommand(job_id=job_id, operation=op, file_id=file_id, working_path=Path("input.xlsx"), selected_engine=EngineMode.EXCEL_COM)
    ctx = ExecutionContext(job_id=job_id, runtime_root=Path("runtime"))
    req = WorkerRequest(job_id=job_id, file_id=file_id, operation_id=op.operation_id, command="execute_operation", payload={"command": cmd.model_dump(mode="json"), "context": ctx.model_dump(mode="json")})
    restored = WorkerRequest.model_validate_json(req.model_dump_json())
    assert restored.payload["command"]["operation"]["opcode"] == "SET_VALUE"
