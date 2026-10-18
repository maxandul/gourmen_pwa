"""Isolated SQLite migration, no existing Drive rows are classified."""
import runpy
from pathlib import Path
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_document_policy_roundtrip():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/r04c120261018_document_policies.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        conn.exec_driver_sql('CREATE TABLE documents (id INTEGER PRIMARY KEY, drive_file_id TEXT)')
        conn.exec_driver_sql("INSERT INTO documents VALUES (1, 'synthetic-old')")
        with Operations.context(MigrationContext.configure(conn)):
            for _ in range(2):
                migration['upgrade']()
                assert conn.exec_driver_sql('SELECT count(*) FROM document_policies').scalar()==0
                assert conn.exec_driver_sql('SELECT drive_file_id FROM documents').scalar()=='synthetic-old'
                migration['downgrade']()
                assert 'document_policies' not in sa.inspect(conn).get_table_names()
    engine.dispose()
