from __future__ import annotations
import json
from contracts.errors import ErrorRecord
from contracts.job import JobSpec
from contracts.result import OperationResult, TransactionRecord, VerificationReport
from contracts.state import JobState
from storage.database import Database
class JobRepository:
    def __init__(self, database: Database) -> None: self.database=database
    def save_job(self, job: JobSpec, state: JobState = JobState.CREATED, workspace_path: str | None = None) -> None:
        self.database.migrate()
        with self.database.connect() as conn:
            with conn:
                conn.execute("INSERT OR REPLACE INTO jobs(job_id,schema_version,state,name,payload_json,workspace_path,updated_at) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", (str(job.job_id), job.schema_version, state.value, job.name, job.model_dump_json(), workspace_path))
                for f in job.files:
                    payload=f.model_dump_json(exclude={'expected_password','write_password'})
                    conn.execute("INSERT OR REPLACE INTO job_files(file_id,job_id,schema_version,source_path,payload_json) VALUES (?,?,?,?,?)", (str(f.file_id), str(job.job_id), f.schema_version, str(f.source_path), payload))
                for op in job.operations:
                    conn.execute("INSERT OR REPLACE INTO job_operations(operation_id,job_id,schema_version,opcode,payload_json) VALUES (?,?,?,?,?)", (str(op.operation_id), str(job.job_id), op.schema_version, op.opcode, op.model_dump_json()))
    def update_state(self, job_id: str, state: JobState, **fields) -> None: self.database.update_job_state(job_id, state.value, **fields)
    def record_error(self, record: ErrorRecord) -> None:
        self.database.migrate(); self.database.insert_json('errors', {'error_id':str(record.error_id),'job_id':str(record.job_id) if record.job_id else None,'file_id':str(record.file_id) if record.file_id else None,'operation_id':str(record.operation_id) if record.operation_id else None,'schema_version':record.schema_version,'code':record.code,'message':record.message,'payload_json':record.model_dump_json()})
    def record_operation_result(self, job_id: str, result: OperationResult) -> None:
        self.database.migrate()
        with self.database.connect() as conn:
            with conn: conn.execute("INSERT INTO operation_results(job_id,operation_id,file_id,schema_version,success,payload_json) VALUES (?,?,?,?,?,?)", (job_id, str(result.operation_id), str(result.file_id), result.schema_version, int(result.success), result.model_dump_json()))
    def record_verification_report(self, report: VerificationReport) -> None:
        self.database.insert_json('verification_reports', {'report_id':str(report.report_id),'job_id':str(report.job_id),'file_id':str(report.file_id) if report.file_id else None,'schema_version':report.schema_version,'status':report.status.value,'payload_json':report.model_dump_json()})
    def record_transaction(self, record: TransactionRecord) -> None:
        self.database.migrate()
        self.database.insert_json('transaction_records', {
            'transaction_id':str(record.transaction_id),
            'job_id':str(record.job_id),
            'file_id':str(record.file_id) if record.file_id else None,
            'schema_version':record.schema_version,
            'stage':record.stage or record.state,
            'path':str(record.path or record.candidate_path or record.working_path or record.committed_path or record.source_path) if (record.path or record.candidate_path or record.working_path or record.committed_path or record.source_path) else None,
            'sha256':record.sha256 or record.committed_sha256 or record.candidate_sha256 or record.source_sha256,
            'atomicity_mode':record.atomicity_mode.value,
            'source_path':str(record.source_path) if record.source_path else None,
            'backup_path':str(record.backup_path) if record.backup_path else None,
            'working_path':str(record.working_path) if record.working_path else None,
            'candidate_path':str(record.candidate_path) if record.candidate_path else None,
            'committed_path':str(record.committed_path) if record.committed_path else None,
            'original_output_backup':str(record.original_output_backup) if record.original_output_backup else None,
            'source_sha256':record.source_sha256,
            'candidate_sha256':record.candidate_sha256,
            'committed_sha256':record.committed_sha256,
            'state':record.state or record.stage,
            'payload_json':record.model_dump_json(),
        })
    def get_payload(self, job_id: str) -> dict | None:
        with self.database.connect() as conn:
            row=conn.execute('SELECT payload_json FROM jobs WHERE job_id=?', (job_id,)).fetchone()
            return None if row is None else json.loads(row[0])
