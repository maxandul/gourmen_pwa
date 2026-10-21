import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.mark.parametrize('field,value',[('private_reminder_hidden','true'),('private_reminder_changed','true'),('private_reminder_version','1')])
def test_reminder_migration_preserves_legacy_and_blocks_used_preferences(field,value):
    spec=importlib.util.spec_from_file_location('migration',Path('migrations/versions/u30120261021_private_reminders.py'))
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    with sa.create_engine('sqlite://').begin() as conn:
        conn.execute(sa.text('CREATE TABLE member_claims (id INTEGER PRIMARY KEY, paid_rappen INTEGER NOT NULL, status TEXT NOT NULL)'))
        conn.execute(sa.text("INSERT INTO member_claims VALUES (1,8400,'beglichen')"))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade()
            assert conn.execute(sa.text('SELECT private_reminder_hidden,private_reminder_changed,private_reminder_version FROM member_claims')).one()==(0,0,0)
            module.downgrade(); module.upgrade()
            conn.execute(sa.text(f'UPDATE member_claims SET {field}={value}'))
            with pytest.raises(RuntimeError,match='preferences exist'): module.downgrade()
            assert conn.execute(sa.text('SELECT paid_rappen,status FROM member_claims')).one()==(8400,'beglichen')
