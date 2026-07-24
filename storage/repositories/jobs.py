from __future__ import annotations
import json
from contracts.job import JobSpec
from contracts.state import JobState
from storage.database import Database
class JobRepository:
    def __init__(self, database: Database) -> None: self.database=database
    def save_job(self, job: JobSpec, state: JobState = JobState.CREATED) -> None:
        self.database.migrate()
        with self.database.connect() as conn:
            with conn:
                conn.execute("INSERT OR REPLACE INTO jobs(job_id,schema_version,state,name,payload_json,updated_at) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)", (str(job.job_id), job.schema_version, state.value, job.name, job.model_dump_json()))
                for f in job.files:
                    payload=f.model_dump_json(exclude={"expected_password","write_password"})
                    conn.execute("INSERT OR REPLACE INTO job_files(file_id,job_id,schema_version,source_path,payload_json) VALUES (?,?,?,?,?)", (str(f.file_id), str(job.job_id), f.schema_version, str(f.source_path), payload))
                for op in job.operations:
                    conn.execute("INSERT OR REPLACE INTO job_operations(operation_id,job_id,schema_version,opcode,payload_json) VALUES (?,?,?,?,?)", (str(op.operation_id), str(job.job_id), op.schema_version, op.opcode, op.model_dump_json()))
    def get_payload(self, job_id: str) -> dict | None:
        with self.database.connect() as conn:
            row=conn.execute("SELECT payload_json FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            return None if row is None else json.loads(row[0])
