import runpy
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_fingerprint_addition_preserves_legacy_and_guards_downgrade():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/u203b20261018_import_fingerprint.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE bank_statement_imports (id INTEGER PRIMARY KEY, filename TEXT)')
        conn.exec_driver_sql("INSERT INTO bank_statement_imports VALUES (1,'synthetic.csv')")
        with Operations.context(MigrationContext.configure(conn)):
            for _ in range(2):
                migration['upgrade']()
                assert conn.exec_driver_sql('SELECT source_fingerprint FROM bank_statement_imports').scalar() is None
                conn.exec_driver_sql("UPDATE bank_statement_imports SET source_fingerprint='synthetic'")
                with pytest.raises(RuntimeError,match='in use'):migration['downgrade']()
                conn.exec_driver_sql('UPDATE bank_statement_imports SET source_fingerprint=NULL')
                migration['downgrade']()
                assert conn.exec_driver_sql('SELECT filename FROM bank_statement_imports').scalar()=='synthetic.csv'
    engine.dispose()
