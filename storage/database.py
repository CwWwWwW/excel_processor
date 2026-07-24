from __future__ import annotations
import sqlite3
from pathlib import Path
SCHEMA_VERSION="1.0"
CORE_TABLES=("jobs","job_files","job_operations","execution_plans","operation_results","change_batches","errors","artifacts","capability_snapshots","workbook_snapshots","verification_reports","task_templates","application_settings","schema_migrations")
MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, schema_version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, schema_version TEXT NOT NULL, state TEXT NOT NULL, name TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS job_files (file_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, schema_version TEXT NOT NULL, source_path TEXT NOT NULL, payload_json TEXT NOT NULL, FOREIGN KEY(job_id) REFERENCES jobs(job_id));
CREATE TABLE IF NOT EXISTS job_operations (operation_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, schema_version TEXT NOT NULL, opcode TEXT NOT NULL, payload_json TEXT NOT NULL, FOREIGN KEY(job_id) REFERENCES jobs(job_id));
CREATE TABLE IF NOT EXISTS execution_plans (job_id TEXT PRIMARY KEY, schema_version TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS operation_results (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, operation_id TEXT NOT NULL, file_id TEXT NOT NULL, schema_version TEXT NOT NULL, success INTEGER NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS change_batches (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, file_id TEXT, schema_version TEXT NOT NULL, storage_path TEXT NOT NULL, row_count INTEGER NOT NULL DEFAULT 0, compressed INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS errors (error_id TEXT PRIMARY KEY, job_id TEXT, file_id TEXT, operation_id TEXT, schema_version TEXT NOT NULL, code TEXT NOT NULL, message TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS artifacts (artifact_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, file_id TEXT NOT NULL, schema_version TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS capability_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, schema_version TEXT NOT NULL, capability_hash TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS workbook_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, file_id TEXT NOT NULL, schema_version TEXT NOT NULL, snapshot_hash TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS verification_reports (report_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, file_id TEXT, schema_version TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS task_templates (template_id TEXT PRIMARY KEY, schema_version TEXT NOT NULL, name TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS application_settings (key TEXT PRIMARY KEY, schema_version TEXT NOT NULL, value_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""
class Database:
    def __init__(self, path: Path) -> None:
        self.path=path; self.path.parent.mkdir(parents=True, exist_ok=True)
    def connect(self) -> sqlite3.Connection:
        conn=sqlite3.connect(self.path); conn.row_factory=sqlite3.Row; conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=ON"); return conn
    def migrate(self) -> None:
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, schema_version TEXT NOT NULL)")
            applied={row[0] for row in conn.execute("SELECT id FROM schema_migrations")}
            if "001_init" not in applied:
                conn.executescript(MIGRATION_SQL); conn.execute("INSERT INTO schema_migrations(id, schema_version) VALUES (?,?)", ("001_init", SCHEMA_VERSION))
            conn.commit()
    def table_names(self) -> set[str]:
        with self.connect() as conn: return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
