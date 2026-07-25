from __future__ import annotations
import json, shutil, sqlite3
from pathlib import Path
from excel_processor.version import DATABASE_SCHEMA_VERSION
SCHEMA_VERSION=DATABASE_SCHEMA_VERSION
CORE_TABLES=("jobs","job_files","job_operations","execution_plans","operation_results","change_batches","errors","artifacts","capability_snapshots","platform_snapshots","workbook_snapshots","verification_reports","task_templates","application_settings","transaction_records","schema_migrations")
MIGRATIONS: tuple[tuple[str,str], ...] = (
('001_init', """
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
"""),
('002_v1_0_1', """
CREATE TABLE IF NOT EXISTS platform_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, schema_version TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS transaction_records (transaction_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, file_id TEXT, schema_version TEXT NOT NULL, stage TEXT NOT NULL, path TEXT, sha256 TEXT, payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_transaction_records_job ON transaction_records(job_id);
CREATE INDEX IF NOT EXISTS idx_errors_job ON errors(job_id);
"""),
('003_transaction_atomicity', """
CREATE INDEX IF NOT EXISTS idx_transaction_records_file ON transaction_records(file_id);
"""),
)
class Database:
    def __init__(self, path: Path) -> None:
        self.path=path; self.path.parent.mkdir(parents=True, exist_ok=True)
    def connect(self) -> sqlite3.Connection:
        conn=sqlite3.connect(self.path); conn.row_factory=sqlite3.Row; conn.execute('PRAGMA journal_mode=WAL'); conn.execute('PRAGMA foreign_keys=ON'); return conn
    def migrate(self) -> None:
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, schema_version TEXT NOT NULL)")
            applied={row[0] for row in conn.execute('SELECT id FROM schema_migrations')}
            for mid, sql in MIGRATIONS:
                if mid not in applied:
                    conn.executescript(sql); conn.execute('INSERT INTO schema_migrations(id, schema_version) VALUES (?,?)',(mid,SCHEMA_VERSION))
            self._ensure_columns(conn)
            conn.commit()
    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        cols={row[1] for row in conn.execute('PRAGMA table_info(jobs)')}
        for name, ddl in {'recovery_state':'TEXT','diagnostics_path':'TEXT','workspace_path':'TEXT'}.items():
            if name not in cols: conn.execute(f'ALTER TABLE jobs ADD COLUMN {name} {ddl}')
        tx_cols={row[1] for row in conn.execute('PRAGMA table_info(transaction_records)')}
        for name, ddl in {
            'atomicity_mode':'TEXT',
            'source_path':'TEXT',
            'backup_path':'TEXT',
            'working_path':'TEXT',
            'candidate_path':'TEXT',
            'committed_path':'TEXT',
            'original_output_backup':'TEXT',
            'source_sha256':'TEXT',
            'candidate_sha256':'TEXT',
            'committed_sha256':'TEXT',
            'state':'TEXT',
        }.items():
            if name not in tx_cols: conn.execute(f'ALTER TABLE transaction_records ADD COLUMN {name} {ddl}')
    def table_names(self) -> set[str]:
        with self.connect() as conn: return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    def integrity_check(self) -> bool:
        with self.connect() as conn: return conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    def update_job_state(self, job_id: str, state: str, **fields) -> None:
        self.migrate(); assignments=['state=?','updated_at=CURRENT_TIMESTAMP']; values=[state]
        for key, value in fields.items(): assignments.append(f'{key}=?'); values.append(str(value) if value is not None else None)
        values.append(job_id)
        with self.connect() as conn:
            with conn: conn.execute(f"UPDATE jobs SET {', '.join(assignments)} WHERE job_id=?", values)
    def insert_json(self, table: str, values: dict) -> None:
        with self.connect() as conn:
            with conn:
                keys=list(values); conn.execute(f"INSERT OR REPLACE INTO {table}({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", [values[k] for k in keys])

def migrate_v1_0_0_runtime(legacy_root: Path, new_db: Database) -> Path | None:
    old_db = legacy_root / 'database' / 'excel_processor.db'
    if not old_db.exists():
        new_db.migrate(); return None
    backup_dir = new_db.path.parent / 'legacy_v1_0_0_backup'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / 'excel_processor.db.readonly.backup'
    if not backup.exists(): shutil.copy2(old_db, backup)
    new_db.migrate()
    with new_db.connect() as conn:
        with conn:
            try: conn.execute("UPDATE jobs SET state='RECOVERY_REQUIRED', recovery_state='RECOVERY_REQUIRED' WHERE state NOT IN ('COMMITTED','CLEANED','ROLLED_BACK')")
            except sqlite3.Error as exc:
                _ = exc
    return backup
