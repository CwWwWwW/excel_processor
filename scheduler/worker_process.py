from __future__ import annotations
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from contracts.errors import ErrorRecord
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from contracts.worker import WorkerRequest, WorkerResponse
from excel_processor.version import WORKER_PROTOCOL_VERSION


@dataclass
class WorkerProcess:
    process: subprocess.Popen
    protocol_version: str
    worker_pid: int


class WorkerProtocolError(RuntimeError):
    """Raised when the Excel worker IPC protocol cannot complete safely."""


class ExcelWorkerClient:
    def __init__(self, module: str = "workers.excel_worker_x64.main", timeout: float = 10.0) -> None:
        self.module = module
        self.timeout = timeout
        self.process_info: WorkerProcess | None = None
        self.excel_pid: int | None = None
        self.excel_hwnd: int | None = None

    @property
    def process(self) -> subprocess.Popen | None:
        return None if self.process_info is None else self.process_info.process

    def start(self) -> None:
        if self.process_info and self.process_info.process.poll() is None:
            return
        self.process_info = start_python_worker(self.module, self.timeout)

    def _send(self, request: WorkerRequest) -> WorkerResponse:
        self.start()
        assert self.process_info is not None
        proc = self.process_info.process
        if proc.stdin is None or proc.stdout is None:
            raise WorkerProtocolError("worker stdio is unavailable")
        proc.stdin.write(request.model_dump_json() + "\n")
        proc.stdin.flush()
        line = _readline_with_timeout(proc, self.timeout)
        if line is None:
            raise WorkerProtocolError("worker response timeout")
        response = WorkerResponse.model_validate_json(line)
        if response.payload.get("excel_pid") is not None:
            self.excel_pid = int(response.payload["excel_pid"])
        if response.payload.get("excel_hwnd") is not None:
            self.excel_hwnd = int(response.payload["excel_hwnd"])
        return response

    def heartbeat(self, job_id: UUID) -> WorkerResponse:
        return self._send(WorkerRequest(job_id=job_id, command="heartbeat"))

    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        request = WorkerRequest(
            job_id=command.job_id,
            file_id=command.file_id,
            operation_id=command.operation.operation_id,
            command="execute_operation",
            payload={"command": command.model_dump(mode="json"), "context": context.model_dump(mode="json")},
        )
        response = self._send(request)
        if not response.success:
            message = response.error.message if response.error else "worker execute_operation failed"
            return OperationResult(operation_id=command.operation.operation_id, file_id=command.file_id, success=False, engine_used=command.selected_engine, errors=(message,))
        return OperationResult.model_validate(response.payload["result"])

    def cancel_operation(self, job_id: UUID) -> WorkerResponse:
        try:
            return self._send(WorkerRequest(job_id=job_id, command="cancel_operation"))
        except WorkerProtocolError:
            self.recycle(kill_owned_excel=True)
            raise

    def shutdown(self) -> None:
        if not self.process_info:
            return
        try:
            self._send(WorkerRequest(job_id=UUID(int=0), command="shutdown"))
        except Exception as exc:
            _ = exc
        proc = self.process_info.process
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.terminate()
        self.process_info = None

    def recycle(self, kill_owned_excel: bool = False) -> None:
        proc = self.process
        if proc is not None and proc.poll() is None:
            proc.terminate()
        if kill_owned_excel and self.excel_pid:
            terminate_owned_excel_pid(self.excel_pid)
        self.process_info = None


class ExcelWorkerPool:
    def __init__(self, module: str = "workers.excel_worker_x64.main", timeout: float = 10.0) -> None:
        self.client = ExcelWorkerClient(module=module, timeout=timeout)

    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        return self.client.execute(command, context)

    def shutdown(self) -> None:
        self.client.shutdown()


def _readline_with_timeout(proc: subprocess.Popen, timeout: float) -> str | None:
    assert proc.stdout is not None
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            return line
        if proc.poll() is not None:
            return None
        time.sleep(0.02)
    return None


def _legacy_response(raw: dict[str, Any], request: WorkerRequest) -> WorkerResponse:
    success = raw.get("type") not in {"error"}
    err = None if success else ErrorRecord(job_id=request.job_id, file_id=request.file_id, operation_id=request.operation_id, code=str(raw.get("code", "WORKER_ERROR")), message=str(raw.get("message", "worker error")))
    return WorkerResponse(request_message_id=request.message_id, job_id=request.job_id, file_id=request.file_id, operation_id=request.operation_id, command=request.command, success=success, payload=raw, error=err)


def start_python_worker(module: str, timeout: float = 5.0) -> WorkerProcess:
    proc = subprocess.Popen([sys.executable, "-m", module], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    assert proc.stdout is not None and proc.stdin is not None
    line = _readline_with_timeout(proc, timeout)
    hello = json.loads(line) if line else None
    if not hello or hello.get("protocol_version") != WORKER_PROTOCOL_VERSION:
        proc.terminate()
        raise WorkerProtocolError("worker handshake failed")
    req = WorkerRequest(job_id=UUID(int=0), command="handshake")
    proc.stdin.write(req.model_dump_json() + "\n")
    proc.stdin.flush()
    response_line = _readline_with_timeout(proc, timeout)
    if response_line is None:
        raise WorkerProtocolError("worker rejected handshake")
    response = WorkerResponse.model_validate_json(response_line)
    if not response.success:
        raise WorkerProtocolError("worker rejected handshake")
    return WorkerProcess(proc, response.protocol_version, int(response.payload.get("worker_pid", proc.pid)))


def terminate_owned_excel_pid(pid: int) -> None:
    # Do not use broad process termination commands. Only terminate the exact Excel PID created by our worker, and only after worker ownership was recorded.
    try:
        import psutil  # type: ignore
    except Exception:
        return
    try:
        process = psutil.Process(pid)
        name = process.name().lower()
        if name == "excel.exe":
            process.terminate()
            process.wait(timeout=5)
    except Exception:
        return
