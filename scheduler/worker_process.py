from __future__ import annotations
import json, subprocess, sys, time
from dataclasses import dataclass
from pathlib import Path
from excel_processor.version import WORKER_PROTOCOL_VERSION
@dataclass
class WorkerProcess:
    process: subprocess.Popen
    protocol_version: str
    worker_pid: int
class WorkerProtocolError(RuntimeError): pass
def start_python_worker(module: str, timeout: float=5.0) -> WorkerProcess:
    proc=subprocess.Popen([sys.executable, '-m', module], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    assert proc.stdout is not None and proc.stdin is not None
    deadline=time.time()+timeout; hello=None
    while time.time()<deadline:
        line=proc.stdout.readline()
        if line:
            hello=json.loads(line); break
    if not hello or hello.get('protocol_version') != WORKER_PROTOCOL_VERSION:
        proc.terminate(); raise WorkerProtocolError('worker handshake failed')
    proc.stdin.write(json.dumps({'type':'handshake','protocol_version':WORKER_PROTOCOL_VERSION})+'\n'); proc.stdin.flush()
    response=json.loads(proc.stdout.readline())
    if response.get('type')!='handshake_ok': raise WorkerProtocolError('worker rejected handshake')
    return WorkerProcess(proc, response.get('protocol_version',''), int(response.get('worker_pid', proc.pid)))
