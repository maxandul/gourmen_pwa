import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_correction_migration_cycle_and_retained_history():
    spec = importlib.util.spec_from_file_location('correction_migration', Path('migrations/versions/u217b120261018_billbro_corrections.py'))
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('CREATE TABLE events (id INTEGER PRIMARY KEY)'))
        conn.execute(sa.text('CREATE TABLE members (id INTEGER PRIMARY KEY)'))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade(); migration.downgrade(); migration.upgrade()
            conn.execute(sa.text("INSERT INTO billbro_corrections (event_id, actor_id, reason, request_hash, before_json, after_json, created_at) VALUES (1, 1, 'Synthetic', 'synthetic-hash', '{}', '{}', '2026-10-18')"))
            with pytest.raises(RuntimeError, match='history'): migration.downgrade()
            assert conn.execute(sa.text('SELECT count(*) FROM billbro_corrections')).scalar() == 1
