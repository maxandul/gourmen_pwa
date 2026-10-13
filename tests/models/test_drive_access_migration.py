"""Run only the additive A-089 migration on an isolated SQLite database."""
import runpy
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from alembic.config import Config


def test_migration_upgrade_downgrade_upgrade_preserves_members():
    root = Path(__file__).resolve().parents[2]
    config = Config()
    config.set_main_option('script_location', str(root / 'migrations'))
    scripts = ScriptDirectory.from_config(config)
    assert len(scripts.get_heads()) == 1
    assert scripts.get_revision('a08920261012') is not None
    migration = runpy.run_path(str(root / 'migrations/versions/a08920261012_drive_access_tasks.py'))
    engine = sa.create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.exec_driver_sql('PRAGMA foreign_keys=ON')
        connection.exec_driver_sql('CREATE TABLE members (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO members VALUES (1)')
        with Operations.context(MigrationContext.configure(connection)):
            migration['upgrade']()
            assert 'drive_access_tasks' in sa.inspect(connection).get_table_names()
            connection.exec_driver_sql("""INSERT INTO drive_access_tasks
                (member_id,email,action,status,attempts,created_at)
                VALUES (1,'synthetic@example.com','revoke','pending',0,CURRENT_TIMESTAMP)""")
            assert connection.exec_driver_sql('SELECT status FROM drive_access_tasks').scalar() == 'pending'
            migration['downgrade']()
            assert 'drive_access_tasks' not in sa.inspect(connection).get_table_names()
            assert connection.exec_driver_sql('SELECT id FROM members').scalar() == 1
            migration['upgrade']()
            assert connection.exec_driver_sql('SELECT count(*) FROM drive_access_tasks').scalar() == 0
    engine.dispose()
