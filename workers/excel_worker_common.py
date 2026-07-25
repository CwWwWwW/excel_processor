from __future__ import annotations
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from uuid import UUID

from contracts.errors import ErrorRecord
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.worker import WorkerRequest, WorkerResponse
from excel_processor.version import WORKER_PROTOCOL_VERSION


@dataclass
class WorkerState:
    job_id: str | None = None
    file_id: str | None = None
    operation_id: str | None = None
    excel_pid: int | None = None
    excel_hwnd: int | None = None
    cancelled: bool = False


def _write(obj) -> None:
    if hasattr(obj, "model_dump_json"):
        text = obj.model_dump_json()
    else:
        text = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def _response(request: WorkerRequest, success: bool, payload: dict | None = None, error: ErrorRecord | None = None) -> WorkerResponse:
    return WorkerResponse(
        request_message_id=request.message_id,
        job_id=request.job_id,
        file_id=request.file_id,
        operation_id=request.operation_id,
        command=request.command,
        success=success,
        payload=payload or {},
        error=error,
    )


def _parse_request(line: str) -> WorkerRequest:
    raw = json.loads(line)
    if "type" in raw and "command" not in raw:
        command_map = {"handshake": "handshake", "heartbeat": "heartbeat", "cancel": "cancel_operation", "execute_probe": "worker_status", "shutdown": "shutdown"}
        command = command_map.get(raw.get("type"), str(raw.get("type")))
        return WorkerRequest(job_id=UUID(str(raw.get("job_id"))) if raw.get("job_id") else UUID(int=0), command=command, payload=raw)
    return WorkerRequest.model_validate(raw)


def run_worker(kind: str) -> int:
    state = WorkerState()
    _write({"type": "hello", "protocol_version": WORKER_PROTOCOL_VERSION, "worker_kind": kind, "worker_pid": os.getpid()})
    for line in sys.stdin:
        try:
            request = _parse_request(line)
            state.job_id = str(request.job_id)
            if request.file_id:
                state.file_id = str(request.file_id)
            if request.operation_id:
                state.operation_id = str(request.operation_id)

            if request.command == "handshake":
                _write(_response(request, True, {"type": "handshake_ok", "protocol_version": WORKER_PROTOCOL_VERSION, "worker_pid": os.getpid()}))
            elif request.command == "heartbeat":
                _write(_response(request, True, {"type": "worker_status", "time": time.time(), "worker_pid": os.getpid(), "excel_pid": state.excel_pid, "excel_hwnd": state.excel_hwnd, "job_id": state.job_id, "file_id": state.file_id, "operation_id": state.operation_id, "cancelled": state.cancelled}))
            elif request.command == "cancel_operation":
                state.cancelled = True
                _write(_response(request, True, {"type": "cancel_acknowledged", "job_id": state.job_id}))
            elif request.command == "worker_status":
                _write(_response(request, True, {"type": "worker_status", "worker_pid": os.getpid(), "excel_pid": state.excel_pid, "excel_hwnd": state.excel_hwnd, "job_id": state.job_id, "file_id": state.file_id, "operation_id": state.operation_id}))
            elif request.command == "execute_operation":
                if state.cancelled:
                    raise RuntimeError("Operation was cancelled before start")
                from engines.com import ExcelComEngine

                command = OperationCommand.model_validate(request.payload["command"])
                context = ExecutionContext.model_validate(request.payload["context"])
                started_payload = {"type": "operation_started", "worker_pid": os.getpid(), "job_id": str(command.job_id), "file_id": str(command.file_id), "operation_id": str(command.operation.operation_id)}
                # Keep the public protocol single-response for clients, but include started metadata in final payload.
                result = ExcelComEngine().execute(command, context)
                _write(_response(request, result.success, {"type": "operation_completed" if result.success else "operation_failed", "operation_started": started_payload, "result": result.model_dump(mode="json"), "worker_pid": os.getpid(), "excel_pid": state.excel_pid, "excel_hwnd": state.excel_hwnd}))
            elif request.command == "shutdown":
                _write(_response(request, True, {"type": "shutdown_ok"}))
                return 0
            else:
                err = ErrorRecord(job_id=request.job_id, file_id=request.file_id, operation_id=request.operation_id, code="UNKNOWN_MESSAGE", message=f"Unknown worker command: {request.command}")
                _write(_response(request, False, {"type": "error"}, err))
        except Exception as exc:
            try:
                request
            except NameError:
                request = WorkerRequest(job_id=UUID(int=0), command="parse_error")
            err = ErrorRecord(job_id=request.job_id, file_id=request.file_id, operation_id=request.operation_id, code="WORKER_EXCEPTION", message=str(exc), details={"traceback": traceback.format_exc()})
            _write(_response(request, False, {"type": "error"}, err))
    return 0
