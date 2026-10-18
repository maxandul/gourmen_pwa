import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.mark.parametrize('new_state', ['teilnahme=NULL', 'billbro_attendance=0', 'billbro_attendance=1'])
def test_attendance_migration_preserves_rsvp_and_refuses_loss(new_state):
    spec = importlib.util.spec_from_file_location('attendance_migration', Path('migrations/versions/u217b3b20261018_attendance.py'))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('CREATE TABLE participations (id INTEGER PRIMARY KEY, teilnahme BOOLEAN NOT NULL, responded_at TEXT)'))
        conn.execute(sa.text("INSERT INTO participations VALUES (1, 1, '2026-01-01'), (2, 0, '2026-02-01')"))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            assert conn.execute(sa.text('SELECT teilnahme, responded_at, billbro_attendance FROM participations ORDER BY id')).all() == [(1, '2026-01-01', None), (0, '2026-02-01', None)]
            migration.downgrade()
            migration.upgrade()
            conn.execute(sa.text('UPDATE participations SET ' + new_state + ' WHERE id=1'))
            before = conn.execute(sa.text('SELECT * FROM participations ORDER BY id')).all()
            with pytest.raises(RuntimeError, match='downgrade refused'):
                migration.downgrade()
            assert conn.execute(sa.text('SELECT * FROM participations ORDER BY id')).all() == before
