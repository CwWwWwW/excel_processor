from storage.database import CORE_TABLES, Database

def test_migrations_are_idempotent(tmp_path):
    db = Database(tmp_path / 'excel_processor.db')
    db.migrate(); db.migrate()
    assert set(CORE_TABLES).issubset(db.table_names())
