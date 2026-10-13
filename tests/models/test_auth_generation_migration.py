"""Additive credential generation migration preserves existing members."""
import runpy
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_upgrade_downgrade_upgrade_preserves_existing_member():
    root = Path(__file__).resolve().parents[2]
    migration = runpy.run_path(str(root / 'migrations/versions/a07720261013_auth_generation.py'))
    engine = sa.create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO members VALUES (1)')
        with Operations.context(MigrationContext.configure(connection)):
            migration['upgrade']()
            assert connection.exec_driver_sql('SELECT id, auth_generation FROM members').one() == (1, '0')
            connection.exec_driver_sql("UPDATE members SET auth_generation='synthetic-generation'")
            migration['downgrade']()
            assert [column['name'] for column in sa.inspect(connection).get_columns('members')] == ['id']
            assert connection.exec_driver_sql('SELECT id FROM members').scalar() == 1
            migration['upgrade']()
            assert connection.exec_driver_sql('SELECT auth_generation FROM members').scalar() == '0'
    engine.dispose()
