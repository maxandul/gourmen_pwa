import runpy
from pathlib import Path
import sqlalchemy as sa
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_additive_allocation_migration_roundtrip():
    migration=runpy.run_path(str(Path(__file__).resolve().parents[2]/'migrations/versions/u202b220261018_payment_allocations.py'))
    engine=sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        for table in ['members','bookings','member_claims']:
            conn.exec_driver_sql(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)')
        conn.exec_driver_sql('CREATE TABLE bank_transactions (id INTEGER PRIMARY KEY, amount_rappen INTEGER)')
        conn.exec_driver_sql('INSERT INTO bank_transactions VALUES (1,1999)')
        with Operations.context(MigrationContext.configure(conn)):
            for _ in range(2):
                migration['upgrade']()
                assert conn.exec_driver_sql('SELECT amount_rappen,allocation_version FROM bank_transactions').one()==(1999,0)
                assert conn.exec_driver_sql('SELECT count(*) FROM bank_payment_allocations').scalar()==0
                conn.exec_driver_sql("INSERT INTO bank_payment_allocations (id,bank_transaction_id,version,position,kind,amount_rappen,created_by,created_at) VALUES (1,1,1,0,'refund',1,1,'2026-01-01')")
                with pytest.raises(RuntimeError,match='not empty'):
                    migration['downgrade']()
                conn.exec_driver_sql('DELETE FROM bank_payment_allocations')
                migration['downgrade']()
        assert conn.exec_driver_sql('SELECT amount_rappen FROM bank_transactions').scalar()==1999
    engine.dispose()
