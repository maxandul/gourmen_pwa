"""A-053: exact bounded prices before article or variant mutation."""
import pytest
from backend.extensions import db
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.services.merch_prices import MerchPriceService, MerchPriceError
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.mark.parametrize('supplier,member,expected',[('19.99','19.99',(1999,1999)),('0','0',(0,0)),('19,99','0.00',(1999,0)),("CHF 1’234.56",'10',(123456,1000))])
def test_price_parser_exact_and_subsidized(supplier,member,expected):
    assert MerchPriceService.form_prices({'base_supplier_price_chf':supplier,'base_member_price_chf':member})==expected


@pytest.mark.parametrize('value',['','-1','NaN','Infinity','0' * 41,'19.999','21474836.48','1e10'])
@pytest.mark.parametrize('field',['base_supplier_price_chf','base_member_price_chf'])
def test_price_parser_rejects_each_field(value,field):
    data={'base_supplier_price_chf':'19.99','base_member_price_chf':'9.99'};data[field]=value
    with pytest.raises(MerchPriceError) as error:MerchPriceService.form_prices(data)
    assert field in error.value.errors


def test_price_parser_no_margin():
    with pytest.raises(MerchPriceError) as error:MerchPriceService.form_prices({'base_supplier_price_chf':'19.99','base_member_price_chf':'20'})
    assert 'base_member_price_chf' in error.value.errors


def data(**changes):
    result=dict(name='Synthetic retained article',description='Retained description',base_supplier_price_chf='19.99',base_member_price_chf='9.99',colors=['Blue'],sizes=['M'],is_active='on')
    result.update(changes);return result


@pytest.fixture
def manager(client,seed):
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    return client


def test_original_create_and_edit_keep_exact_prices(app,manager):
    assert manager.post('/admin/merch/articles/new',data=data()).status_code==302
    with app.app_context():
        article=MerchArticle.query.one();aid=article.id
        assert (article.base_supplier_price_rappen,article.base_member_price_rappen)==(1999,999)
        assert MerchVariant.query.one().supplier_price_rappen==1999
    assert manager.post(f'/admin/merch/articles/{aid}/edit',data=data(base_supplier_price_chf='20.01',base_member_price_chf='0')).status_code==302
    with app.app_context():
        article=db.session.get(MerchArticle,aid);assert (article.base_supplier_price_rappen,article.base_member_price_rappen)==(2001,0)
        assert MerchVariant.query.one().member_price_rappen==0


@pytest.mark.parametrize('mode',['create','edit'])
@pytest.mark.parametrize('value',['-5','NaN','19.999','21474836.48','20.00'])
def test_invalid_price_preserves_form_and_database(app,manager,mode,value):
    url='/admin/merch/articles/new'
    if mode=='edit':
        assert manager.post(url,data=data()).status_code==302
        with app.app_context():aid=MerchArticle.query.one().id;vid=MerchVariant.query.one().id
        url=f'/admin/merch/articles/{aid}/edit'
    response=manager.post(url,data=data(name='Must stay in input',base_member_price_chf=value,colors=['Navy'],sizes=['XL']))
    assert response.status_code==400 and 'Must stay in input' in response.text and value in response.text
    assert 'form-field__error' in response.text and 'Navy' in response.text and 'XL' in response.text
    with app.app_context():
        if mode=='create':assert MerchArticle.query.count()==0 and MerchVariant.query.count()==0
        else:
            article=db.session.get(MerchArticle,aid);variant=db.session.get(MerchVariant,vid)
            assert article.name=='Synthetic retained article' and article.base_member_price_rappen==999
            assert variant.color=='Blue' and variant.size=='M' and variant.member_price_rappen==999
