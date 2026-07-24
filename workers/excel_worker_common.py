from __future__ import annotations
import json, os, sys, time, traceback
from dataclasses import dataclass
from excel_processor.version import WORKER_PROTOCOL_VERSION
from engines.com.session import ExcelComSession
@dataclass
class WorkerState:
    job_id: str | None=None
    excel_pid: int | None=None
    excel_hwnd: int | None=None
    cancelled: bool=False
def _send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + '\n'); sys.stdout.flush()
def run_worker(kind: str) -> int:
    state=WorkerState(); _send({'type':'hello','protocol_version':WORKER_PROTOCOL_VERSION,'worker_kind':kind,'worker_pid':os.getpid()})
    for line in sys.stdin:
        try:
            msg=json.loads(line); mtype=msg.get('type')
            if mtype=='handshake': _send({'type':'handshake_ok','protocol_version':WORKER_PROTOCOL_VERSION,'worker_pid':os.getpid()})
            elif mtype=='heartbeat': _send({'type':'heartbeat_ok','time':time.time(),'worker_pid':os.getpid(),'excel_pid':state.excel_pid,'excel_hwnd':state.excel_hwnd,'job_id':state.job_id})
            elif mtype=='cancel': state.cancelled=True; _send({'type':'cancelled','job_id':state.job_id})
            elif mtype=='execute_probe':
                state.job_id=msg.get('job_id')
                with ExcelComSession(visible=False, allow_macros=False) as session:
                    state.excel_pid=session.excel_pid; state.excel_hwnd=session.hwnd
                    _send({'type':'probe_ok','worker_pid':os.getpid(),'excel_pid':state.excel_pid,'excel_hwnd':state.excel_hwnd,'job_id':state.job_id})
            elif mtype=='shutdown': _send({'type':'shutdown_ok'}); return 0
            else: _send({'type':'error','code':'UNKNOWN_MESSAGE','message':f'?? worker ???{mtype}'})
        except Exception as exc:
            _send({'type':'error','code':'WORKER_EXCEPTION','message':str(exc),'traceback':traceback.format_exc()})
    return 0
