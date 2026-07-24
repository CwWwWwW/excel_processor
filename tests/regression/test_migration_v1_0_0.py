import sqlite3
from storage.database import Database, migrate_v1_0_0_runtime

def test_legacy_runtime_backup_and_new_schema(tmp_path):
    legacy=tmp_path/'runtime'; old=legacy/'database'/'excel_processor.db'; old.parent.mkdir(parents=True)
    conn=sqlite3.connect(old); conn.execute("CREATE TABLE jobs(job_id TEXT PRIMARY KEY, schema_version TEXT, state TEXT, name TEXT, payload_json TEXT)"); conn.commit(); conn.close()
    db=Database(tmp_path/'local'/'database'/'excel_processor.db')
    backup=migrate_v1_0_0_runtime(legacy, db)
    assert backup and backup.exists()
    assert 'platform_snapshots' in db.table_names()
