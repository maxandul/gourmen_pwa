"""Normalized uniqueness and collision preflight without editing legacy addresses."""
import runpy
from pathlib import Path
import sqlalchemy as sa
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_normalized_email_index_roundtrip_and_conflicts():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/r05b20261018_primary_email_index.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY,email TEXT NOT NULL UNIQUE)')
        original=' Mixed@Example.com '
        conn.execute(sa.text('INSERT INTO members VALUES (1,:email)'),{'email':original})
        with Operations.context(MigrationContext.configure(conn)):
            migration['upgrade']()
            assert conn.exec_driver_sql('SELECT email FROM members').scalar()==original
            for email in ['mixed@example.com',' MIXED@example.com ','\tMixed@example.com\n']:
                with pytest.raises(sa.exc.IntegrityError):conn.execute(sa.text('INSERT INTO members VALUES (2,:email)'),{'email':email})
            migration['downgrade']();migration['upgrade']();migration['downgrade']()
            conn.exec_driver_sql("INSERT INTO members VALUES (2,'mixed@example.com')")
            with pytest.raises(RuntimeError,match='reconcile explicitly'):migration['upgrade']()
            assert conn.exec_driver_sql('SELECT count(*) FROM members').scalar()==2
    engine.dispose()
