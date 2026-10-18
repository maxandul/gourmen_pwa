import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.mark.parametrize('legacy_points', [False, True])
def test_fractional_migration_both_legacy_shapes_and_safe_downgrade(legacy_points):
    spec = importlib.util.spec_from_file_location('fractional_migration', Path('migrations/versions/u217b220261018_ggl_fractional.py'))
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('CREATE TABLE participations (id INTEGER PRIMARY KEY, rank INTEGER' + (', points INTEGER' if legacy_points else '') + ')'))
        conn.execute(sa.text('INSERT INTO participations (id, rank) VALUES (1, 2)'))
        if legacy_points: conn.execute(sa.text('UPDATE participations SET points=3'))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            assert conn.execute(sa.text('SELECT rank, points FROM participations')).one() == (2, 3 if legacy_points else None)
            migration.downgrade(); migration.upgrade()
            conn.execute(sa.text('UPDATE participations SET rank=1.5, points=2.5'))
            with pytest.raises(RuntimeError, match='Fractional'): migration.downgrade()
            assert conn.execute(sa.text('SELECT rank, points FROM participations')).one() == (1.5, 2.5)
