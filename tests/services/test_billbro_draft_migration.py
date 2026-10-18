import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_draft_migration_roundtrip_and_history_guard():
    spec = importlib.util.spec_from_file_location('draft_migration', Path('migrations/versions/u217c1a20261018_billbro_drafts.py'))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('CREATE TABLE events (id INTEGER PRIMARY KEY)'))
        conn.execute(sa.text('CREATE TABLE members (id INTEGER PRIMARY KEY)'))
        conn.execute(sa.text('INSERT INTO events VALUES (1)'))
        conn.execute(sa.text('INSERT INTO members VALUES (1)'))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            migration.downgrade()
            migration.upgrade()
            conn.execute(sa.text("INSERT INTO billbro_correction_drafts (event_id,actor_id,request_hash,before_json,proposal_json,preview_json,created_at,status) VALUES (1,1,'synthetic','{}','{}','{}','2026-10-18','pending')"))
            with pytest.raises(RuntimeError, match='draft history'):
                migration.downgrade()
            assert conn.execute(sa.text('SELECT status FROM billbro_correction_drafts')).scalar() == 'pending'
