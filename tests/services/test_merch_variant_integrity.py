"""Stable catalogue identities and honest description provenance."""
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_description_migration_cycle_and_history_guard():
    spec=importlib.util.spec_from_file_location('merch_description_migration',Path('migrations/versions/u21420261018_merch_item_description.py'))
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(sa.text('CREATE TABLE merch_order_items (id INTEGER PRIMARY KEY)'))
        connection.execute(sa.text('INSERT INTO merch_order_items (id) VALUES (1)'))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            assert connection.execute(sa.text('SELECT description_snapshot FROM merch_order_items')).scalar() is None
            migration.downgrade();migration.upgrade()
            connection.execute(sa.text("UPDATE merch_order_items SET description_snapshot='Synthetic retained description',description_snapshot_source='order'"))
            with pytest.raises(RuntimeError,match='history'):migration.downgrade()
            assert connection.execute(sa.text('SELECT description_snapshot FROM merch_order_items')).scalar()=='Synthetic retained description'


from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_order_item import MerchOrderItem
from tests.routes.test_merch_read_only import catalogue
from tests.services.test_audit_failure_boundary import seed


def form(**changes):
    value=dict(name='Renamed catalogue',base_supplier_price_chf='30',base_member_price_chf='25',colors=['ActiveBlue'],sizes=['M'],is_active='on')
    value.update(changes);return value


@pytest.mark.parametrize('status',list(OrderStatus))
def test_edit_preserves_order_and_variant_history(app,client,catalogue,status):
    aid,active,old,oid,itemid=catalogue
    with app.app_context():
        order=db.session.get(MerchOrder,oid);order.status=status;db.session.commit()
    response=client.post(f'/admin/merch/articles/{aid}/edit',data=form())
    assert response.status_code==302
    with app.app_context():
        assert MerchVariant.query.count()==2
        assert db.session.get(MerchVariant,active).supplier_price_rappen==2000
        assert not db.session.get(MerchVariant,old).is_active
        item=db.session.get(MerchOrderItem,itemid)
        assert item.variant_id==old and item.total_member_price_rappen==1900
        assert item.description_snapshot=='Synthetic catalogue HistoricalRed XL'
        assert item.description_snapshot_source=='legacy_catalogue'
        assert 'Altbestand' in item.display_name and 'Renamed' not in item.display_name
        assert db.session.get(MerchOrder,oid).status==status
    assert client.post(f'/admin/merch/articles/{aid}/edit',data=form(name='Renamed again')).status_code==302
    with app.app_context():assert db.session.get(MerchOrderItem,itemid).description_snapshot=='Synthetic catalogue HistoricalRed XL'


def test_deactivate_and_reactivate_same_id_and_price(app,client,catalogue):
    aid,active,old,_,_=catalogue
    assert client.post(f'/admin/merch/articles/{aid}/edit',data=form(colors=['Green'],sizes=['L'])).status_code==302
    with app.app_context():
        assert not db.session.get(MerchVariant,active).is_active
        new=MerchVariant.query.filter_by(color='Green').one();assert new.member_price_rappen==2500
    assert client.post(f'/admin/merch/articles/{aid}/edit',data=form(colors=[' activeblue ', 'ACTIVEBLUE'],sizes=[' m ', 'M'])).status_code==302
    with app.app_context():
        assert MerchVariant.query.count()==3
        original=db.session.get(MerchVariant,active)
        assert original.is_active and original.color=='ActiveBlue' and original.size=='M' and original.member_price_rappen==1500


def test_duplicate_normalized_new_choices_create_one_variant(app,client,catalogue):
    response=client.post('/admin/merch/articles/new',data=form(name='Deduplicated',colors=[' Navy  Blue ','navy blue'],sizes=['XL',' xl ']))
    assert response.status_code==302
    with app.app_context():
        article=MerchArticle.query.filter_by(name='Deduplicated').one()
        variant=MerchVariant.query.filter_by(article_id=article.id).one()
        assert (variant.color,variant.size)==('Navy Blue','XL')


@pytest.mark.parametrize('field,value',[('colors',['']),('colors',['X'*51]),('sizes',[' ']),('sizes',['X'*21]),('name','')])
def test_invalid_selection_keeps_article_and_history(app,client,catalogue,field,value):
    response=client.post(f'/admin/merch/articles/{catalogue[0]}/edit',data=form(**{field:value}))
    assert response.status_code==400
    with app.app_context():
        assert db.session.get(MerchArticle,catalogue[0]).name=='Synthetic catalogue'
        assert MerchVariant.query.count()==2 and db.session.get(MerchOrderItem,catalogue[4]).description_snapshot is None


def test_ambiguous_legacy_variants_are_not_merged(app,client,catalogue):
    with app.app_context():
        db.session.add(MerchVariant(article_id=catalogue[0],color=' activeblue ',size='m',supplier_price_rappen=7777,member_price_rappen=1111,is_active=False));db.session.commit()
    response=client.post(f'/admin/merch/articles/{catalogue[0]}/edit',data=form())
    assert response.status_code==400 and 'mehrdeutige alte Varianten' in response.text
    with app.app_context():
        assert MerchVariant.query.count()==3 and db.session.get(MerchArticle,catalogue[0]).name=='Synthetic catalogue'
        assert db.session.get(MerchOrderItem,catalogue[4]).variant_id==catalogue[2]


def test_commit_failure_restores_catalogue_and_snapshots(app,client,catalogue,monkeypatch):
    def fail():raise sa.exc.OperationalError('synthetic',{},Exception('synthetic'))
    monkeypatch.setattr(db.session,'commit',fail)
    response=client.post(f'/admin/merch/articles/{catalogue[0]}/edit',data=form(colors=['Green']))
    assert response.status_code==400 and 'Renamed catalogue' in response.text
    with app.app_context():
        assert db.session.get(MerchArticle,catalogue[0]).name=='Synthetic catalogue'
        assert db.session.get(MerchOrderItem,catalogue[4]).description_snapshot is None
        assert MerchVariant.query.count()==2 and db.session.get(MerchVariant,catalogue[1]).is_active


def test_new_order_captures_description_before_later_rename(app,client,catalogue):
    aid=catalogue[0]
    response=client.post('/member/merch/order',data={f'color_{aid}[]':['ActiveBlue'],f'size_{aid}[]':['M'],f'quantity_{aid}[]':['1']})
    assert response.status_code==302
    with app.app_context():
        item=MerchOrderItem.query.filter_by(variant_id=catalogue[1]).one();iid=item.id
        assert item.description_snapshot=='Synthetic catalogue ActiveBlue M' and item.description_snapshot_source=='order'
    assert client.post(f'/admin/merch/articles/{aid}/edit',data=form()).status_code==302
    with app.app_context():assert db.session.get(MerchOrderItem,iid).display_name=='Synthetic catalogue ActiveBlue M'


@pytest.mark.parametrize('edit',[False,True])
def test_ambiguous_order_selection_rolls_back_all_items(app,client,catalogue,edit):
    aid=catalogue[0]
    with app.app_context():
        db.session.add(MerchVariant(article_id=aid,color=' activeblue ',size='m',supplier_price_rappen=9999,member_price_rappen=8888,is_active=True));db.session.commit()
    url=f'/member/merch/order/{catalogue[3]}/edit' if edit else '/member/merch/order'
    response=client.post(url,data={f'color_{aid}[]':['ActiveBlue'],f'size_{aid}[]':['M'],f'quantity_{aid}[]':['1']})
    assert response.status_code==200 and 'nicht eindeutig' in response.text
    with app.app_context():
        assert MerchOrder.query.count()==1 and MerchOrderItem.query.count()==1
        assert db.session.get(MerchOrderItem,catalogue[4]).variant_id==catalogue[2]
