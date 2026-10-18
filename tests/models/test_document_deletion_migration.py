"""Deletion journal roundtrip and repeat protection on isolated SQLite."""
import runpy
from pathlib import Path
import sqlalchemy as sa
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_deletion_migration_roundtrip():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/r04c320261018_document_deletion.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        conn.exec_driver_sql('INSERT INTO members VALUES (1)')
        with Operations.context(MigrationContext.configure(conn)):
            migration['upgrade']()
            sql="INSERT INTO document_deletion_requests VALUES ('fake',1,1,'test.pdf','review','2026-10-18',NULL,'pending')"
            conn.exec_driver_sql(sql)
            with pytest.raises(sa.exc.IntegrityError):conn.exec_driver_sql(sql)
            migration['downgrade']();migration['upgrade']()
            assert conn.exec_driver_sql('SELECT count(*) FROM document_deletion_requests').scalar()==0
            assert conn.exec_driver_sql('SELECT count(*) FROM members').scalar()==1
    engine.dispose()
