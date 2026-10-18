"""Reversible isolated grant schema and active uniqueness, no real DB."""
import runpy
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_grant_migration_roundtrip_and_active_unique():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/r04b120261018_member_area_grants.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO members VALUES (1)')
        with Operations.context(MigrationContext.configure(connection)):
            migration['upgrade']()
            sql="INSERT INTO member_area_grants (member_id,scope,granted_by,granted_at) VALUES (1,'travel_documents',1,'2026-10-18')"
            connection.exec_driver_sql(sql)
            with pytest.raises(sa.exc.IntegrityError):connection.exec_driver_sql(sql)
            connection.exec_driver_sql("UPDATE member_area_grants SET revoked_at='2026-10-18',revoked_by=1")
            connection.exec_driver_sql(sql)
            assert connection.exec_driver_sql('SELECT count(*) FROM member_area_grants').scalar()==2
            migration['downgrade']()
            assert 'member_area_grants' not in sa.inspect(connection).get_table_names()
            assert connection.exec_driver_sql('SELECT id FROM members').scalar()==1
            migration['upgrade']()
            assert connection.exec_driver_sql('SELECT count(*) FROM member_area_grants').scalar()==0
    engine.dispose()
