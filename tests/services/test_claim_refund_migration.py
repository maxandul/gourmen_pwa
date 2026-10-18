import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_claim_refund_migration_cycle_and_history_guard():
    spec = importlib.util.spec_from_file_location('migration', Path('migrations/versions/u217c1b120261018_claim_refund_payments.py'))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('PRAGMA foreign_keys=ON'))
        for table in ('member_claims', 'billbro_corrections', 'bank_payment_allocations'):
            conn.execute(sa.text(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)'))
            conn.execute(sa.text(f'INSERT INTO {table} VALUES (1)'))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade(); migration.downgrade(); migration.upgrade()
            conn.execute(sa.text('INSERT INTO claim_refund_payments (claim_id,correction_id,allocation_id) VALUES (1,1,1)'))
            with pytest.raises(RuntimeError, match='refund history'): migration.downgrade()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text('DELETE FROM member_claims WHERE id=1'))
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text('INSERT INTO claim_refund_payments (claim_id,correction_id,allocation_id) VALUES (1,1,1)'))
            assert conn.execute(sa.text('SELECT count(*) FROM claim_refund_payments')).scalar() == 1
