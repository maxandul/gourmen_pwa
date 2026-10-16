import runpy
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_nullable_snapshots_preserve_legacy_tokens():
    migration = runpy.run_path(str(Path(__file__).resolve().parents[2] /
                                  'migrations/versions/a13920261016_onboarding_delivery.py'))
    engine = sa.create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE auth_tokens (id INTEGER PRIMARY KEY, token_hash VARCHAR(128))')
        connection.exec_driver_sql("INSERT INTO auth_tokens VALUES (1, 'synthetic')")
        with Operations.context(MigrationContext.configure(connection)):
            migration['upgrade']()
            snapshot = connection.exec_driver_sql(
                'SELECT recipient_email, issued_generation, delivery_status FROM auth_tokens').one()
            assert snapshot == (None, None, None)
            migration['downgrade']()
            assert connection.exec_driver_sql('SELECT * FROM auth_tokens').one() == (1, 'synthetic')
            migration['upgrade']()
    engine.dispose()
