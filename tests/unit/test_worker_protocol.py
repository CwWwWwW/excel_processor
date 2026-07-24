from scheduler.worker_process import start_python_worker

def test_worker_handshake():
    worker = start_python_worker('workers.excel_worker_x64.main')
    try:
        assert worker.protocol_version == '1.0.1'
        assert worker.worker_pid > 0
    finally:
        worker.process.stdin.write('{"type":"shutdown"}\n')
        worker.process.stdin.flush()
        worker.process.wait(timeout=5)
