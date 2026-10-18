"""Strict synthetic CSV validation, no invented collective amounts."""
import csv
import io
import pytest
from backend.extensions import db
from backend.models.accounting import BankStatementImport,BankTransaction
from backend.models.member import Member
from backend.services.bank_import import BankImportService,BankImportError,parse_chf_to_rappen
from tests.services.test_bank_booking_atomicity import case

HEADER=['Datum','Buchungstext','Whg','Betrag Detail','ZKB-Referenz','Referenznummer',
        'Belastung CHF','Gutschrift CHF','Valuta','Saldo CHF','Zahlungszweck','Details']


def main(**changes):
    row=dict.fromkeys(HEADER,'');row.update({'Datum':'01.06.2026','Buchungstext':'Synthetic',
        'ZKB-Referenz':'synthetic-csv','Gutschrift CHF':'100.00','Valuta':'01.06.2026'})
    row.update(changes);return row


def detail(amount='40.00',currency='CHF'):
    row=dict.fromkeys(HEADER,'');row.update({'Buchungstext':'Synthetic recipient','Whg':currency,'Betrag Detail':amount});return row


def payload(rows,header=HEADER):
    stream=io.StringIO();writer=csv.writer(stream,delimiter=';');writer.writerow(header)
    for row in rows:writer.writerow([row.get(key,'') for key in header])
    return stream.getvalue().encode('utf-8')


def collective(rows,**changes):
    return payload([main(**{'Buchungstext':'Gutschriften eBanking (2)',**changes}),*rows])


@pytest.mark.parametrize('raw',['abc','NaN','Infinity','--2','+-2','1.001','1,20',"12'34.00",'21474836.48'])
def test_invalid_amount_format_is_explicit(raw):
    with pytest.raises(ValueError):parse_chf_to_rappen(raw)
    with pytest.raises(BankImportError,match='Datensatz 2, Gutschrift CHF'):
        BankImportService.parse_csv(payload([main(**{'Gutschrift CHF':raw})]))


@pytest.mark.parametrize('rows',[[detail()], [detail('40'),detail('50')],
    [detail('40'),detail('60'),detail('1')],[],[detail('0'),detail('100')],
    [detail('40','CHF'),detail('60','EUR')]])
def test_incomplete_or_conflicting_collective_rejected(rows):
    with pytest.raises(BankImportError):BankImportService.parse_csv(collective(rows))


def test_complete_chf_collective_never_changes_amounts():
    parent=BankImportService.parse_csv(collective([detail('40'),detail('60')]))[0]
    assert [row.amount_rappen for row in parent.detail_rows]==[4000,6000]


def test_verified_foreign_total_preserves_bank_sum():
    parent=BankImportService.parse_csv(collective([detail('40','EUR'),detail('60','EUR')],
        **{'Buchungstext':'Gutschriften eBanking (2), EUR 100.00','Gutschrift CHF':'92.01'}))[0]
    assert [row.amount_rappen for row in parent.detail_rows]==[3680,5521]
    assert sum(row.amount_rappen for row in parent.detail_rows)==parent.amount_rappen


@pytest.mark.parametrize('heading',['Gutschriften eBanking (2)',
    'Gutschriften eBanking (2), EUR 200.00','Gutschriften eBanking (2), USD 100.00'])
def test_foreign_group_requires_matching_declared_total(heading):
    with pytest.raises(BankImportError):
        BankImportService.parse_csv(collective([detail('40','EUR'),detail('60','EUR')],**{'Buchungstext':heading}))


@pytest.mark.parametrize('rows',[[detail()], [main(**{'Gutschrift CHF':'','Belastung CHF':''})],
    [main(**{'Belastung CHF':'1'})],[main(**{'Datum':'not-a-date'})],
    [main(**{'Buchungstext':'Gutschriften eBanking (?)'})]])
def test_malformed_rows_are_not_silently_skipped(rows):
    with pytest.raises(BankImportError):BankImportService.parse_csv(payload(rows))


def test_required_and_duplicate_columns_rejected():
    for header in [HEADER[:-1],HEADER+['Datum']]:
        with pytest.raises(BankImportError,match='Spalten'):
            BankImportService.parse_csv(payload([main()],header))


def test_malformed_quote_rejected():
    with pytest.raises(BankImportError,match='CSV-Struktur'):
        BankImportService.parse_csv(payload([])+b'"unterminated')


def test_original_upload_reports_bad_second_row_without_partial_import(app,client,case):
    from tests.conftest import auth_id
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True
    bad=payload([main(),main(**{'Gutschrift CHF':'abc'})])
    response=client.post('/accounting/import',data={'file':(io.BytesIO(bad),'synthetic.csv')},
        content_type='multipart/form-data')
    assert response.status_code==302
    with client.session_transaction() as state:
        assert any('Datensatz 3, Gutschrift CHF' in text for _,text in state.get('_flashes',[]))
    with app.app_context():
        assert BankTransaction.query.count()==1 and BankStatementImport.query.count()==1
