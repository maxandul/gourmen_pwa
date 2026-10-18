"""Original catalogue GETs must never schedule variant deletions."""
import pytest
from sqlalchemy import event as sa_event
from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_order_item import MerchOrderItem
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.fixture
def catalogue(app,client,seed):
    with app.app_context():
        article=MerchArticle(name='Synthetic catalogue',base_supplier_price_rappen=2000,base_member_price_rappen=1500)
        db.session.add(article);db.session.flush()
        active=MerchVariant(article_id=article.id,color='ActiveBlue',size='M',supplier_price_rappen=2000,member_price_rappen=1500,is_active=True)
        old=MerchVariant(article_id=article.id,color='HistoricalRed',size='XL',supplier_price_rappen=2500,member_price_rappen=1900,is_active=False)
        db.session.add_all([active,old]);db.session.flush()
        order=MerchOrder(member_id=seed[0],order_number='SYNTHETIC-READ',status=OrderStatus.BESTELLT,total_member_price_rappen=1900,total_supplier_price_rappen=2500,total_profit_rappen=-600)
        db.session.add(order);db.session.flush()
        item=MerchOrderItem(order_id=order.id,article_id=article.id,variant_id=old.id,quantity=1,unit_member_price_rappen=1900,unit_supplier_price_rappen=2500,total_member_price_rappen=1900,total_supplier_price_rappen=2500,total_profit_rappen=-600)
        db.session.add(item);db.session.commit();ids=(article.id,active.id,old.id,order.id,item.id)
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    return ids


@pytest.mark.parametrize('path',['/member/merch','/member/merch/order','/member/merch/order/{order}/edit'])
def test_get_with_historical_variant_performs_no_dml(app,client,catalogue,path):
    statements=[]
    def record(conn,cursor,statement,parameters,context,executemany):statements.append(statement.lstrip().upper())
    with app.app_context():engine=db.engine
    sa_event.listen(engine,'before_cursor_execute',record)
    try:
        response=client.get(path.format(order=catalogue[3]))
        assert response.status_code==200
        assert 'ActiveBlue' in response.text
        assert not any(sql.startswith(('INSERT','UPDATE','DELETE')) for sql in statements)
    finally:sa_event.remove(engine,'before_cursor_execute',record)
    with app.app_context():
        article=db.session.get(MerchArticle,catalogue[0]);assert len(article.variants)==2
        assert db.session.get(MerchVariant,catalogue[2]).color=='HistoricalRed'
        item=db.session.get(MerchOrderItem,catalogue[4]);assert item.variant_id==catalogue[2] and item.total_member_price_rappen==1900


@pytest.mark.parametrize('count',[3,30])
def test_shop_catalogue_query_scaling(app,client,seed,count):
    with app.app_context():
        for index in range(count):
            article=MerchArticle(name=f'Synthetic {index}',base_supplier_price_rappen=2000,base_member_price_rappen=1500)
            db.session.add(article);db.session.flush()
            db.session.add(MerchVariant(article_id=article.id,color='Blue',size='M',supplier_price_rappen=2000,member_price_rappen=1500,is_active=True))
        db.session.commit();engine=db.engine
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    statements=[]
    def record(conn,cursor,statement,parameters,context,executemany):statements.append(statement.lower())
    sa_event.listen(engine,'before_cursor_execute',record)
    try:assert client.get('/member/merch').status_code==200
    finally:sa_event.remove(engine,'before_cursor_execute',record)
    variant_queries=[sql for sql in statements if 'from merch_variants' in sql]
    print(f'articles={count}; total_sql={len(statements)}; variant_queries={len(variant_queries)}')
    assert len(variant_queries)==1
