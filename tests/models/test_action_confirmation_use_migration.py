"""Additive receipt table, unique consumption and reversible isolated schema."""
import runpy
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_receipt_migration_and_unique_consumption():
    path = Path(__file__).resolve().parents[2] / 'migrations/versions/f120261016_action_confirmation_uses.py'
    migration = runpy.run_path(str(path))
    engine = sa.create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO members VALUES (1)')
        with Operations.context(MigrationContext.configure(connection)):
            migration['upgrade']()
            statement = "INSERT INTO action_confirmation_uses VALUES ('synthetic-hash', '2026-10-16')"
            connection.exec_driver_sql(statement)
            with pytest.raises(sa.exc.IntegrityError):
                connection.exec_driver_sql(statement)
            migration['downgrade']()
            assert 'action_confirmation_uses' not in sa.inspect(connection).get_table_names()
            assert connection.exec_driver_sql('SELECT id FROM members').scalar() == 1
            migration['upgrade']()
            assert connection.exec_driver_sql('SELECT COUNT(*) FROM action_confirmation_uses').scalar() == 0
    engine.dispose()
