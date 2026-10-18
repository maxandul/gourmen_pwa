"""Reference-less rows remain distinct; ambiguity never silently drops money."""
import io
from unittest.mock import Mock
import pytest
from backend.extensions import db
from backend.models.accounting import BankStatementImport,BankTransaction,FiscalYear
from backend.models.member import Member
from backend.services.bank_import import BankImportService as Service,BankImportError
from tests.services.test_bank_csv_validation import main,payload


class Upload(io.BytesIO):
    filename='synthetic.csv'


@pytest.fixture
def importer(app):
    with app.app_context():
        member=Member(vorname='Synthetic',nachname='Import',email='identity@example.com')
        member.set_password('Synthetic-import-password!');db.session.add(member);db.session.commit()
        return member.id


def import_data(data,uid):
    return Service.import_statement(Upload(data),db.session.get(Member,uid))


def unreferenced(**changes):
    return main(**{'ZKB-Referenz':'',**changes})


def test_different_purpose_and_identical_occurrences_are_preserved(app,importer):
    data=payload([unreferenced(**{'Zahlungszweck':'Invoice A'}),
        unreferenced(**{'Zahlungszweck':'Invoice B'}),unreferenced(),unreferenced()])
    with app.app_context():
        first=import_data(data,importer)
        assert first.new_count==4 and first.duplicate_count==0
        keys=[row.line_key for row in BankTransaction.query.all()]
        assert len(set(keys))==4 and all(key.startswith('H2') for key in keys)
        assert sum(row.amount_rappen for row in BankTransaction.query.all())==40000
        second=import_data(data,importer)
        assert second.new_count==0 and second.duplicate_count==4
        assert BankTransaction.query.count()==4


def test_different_file_collision_is_explicit_and_atomic(app,importer):
    data=payload([unreferenced()])
    changed=payload([main(**{'ZKB-Referenz':'new-before-collision'}),unreferenced()])
    with app.app_context():
        import_data(data,importer)
        with pytest.raises(BankImportError,match='anderer Datei'):
            import_data(changed,importer)
        assert BankStatementImport.query.count()==1 and BankTransaction.query.count()==1
        assert BankTransaction.query.filter_by(line_key='new-before-collision').first() is None


def test_legacy_weak_identity_is_not_silently_migrated(app,importer):
    data=payload([unreferenced()])
    with app.app_context():
        import_data(data,importer)
        parsed=Service.parse_csv(data)[0]
        tx=BankTransaction.query.one();tx.line_key=Service._legacy_content_key(parsed)
        tx.statement_import.source_fingerprint=None;db.session.commit()
        with pytest.raises(BankImportError,match='alten Ersatzschlüssel'):
            import_data(data,importer)
        assert BankTransaction.query.count()==1 and BankStatementImport.query.count()==1
        assert tx.line_key.startswith('H') and not tx.line_key.startswith('H2')


def test_same_bank_reference_with_changed_amount_is_not_a_duplicate(app,importer):
    with app.app_context():
        import_data(payload([main()]),importer)
        with pytest.raises(BankImportError,match='abweichende Daten'):
            import_data(payload([main(**{'Gutschrift CHF':'101.00'})]),importer)
        assert BankTransaction.query.one().amount_rappen==10000
        assert BankStatementImport.query.count()==1


@pytest.mark.parametrize('failure',['second_insert','commit'])
def test_failed_import_has_no_partial_header_year_or_rows(app,importer,monkeypatch,failure):
    data=payload([main(),main(**{'ZKB-Referenz':'second'})])
    with app.app_context():
        with monkeypatch.context() as patch:
            if failure=='commit':
                patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            else:
                original=Service._create_transaction
                calls=[]
                def fail(*args,**kwargs):
                    row=original(*args,**kwargs);calls.append(row)
                    if len(calls)==2:
                        row.buchungstext=None;db.session.flush()
                    return row
                patch.setattr(Service,'_create_transaction',fail)
            with pytest.raises(BankImportError,match='nicht bestätigt'):
                import_data(data,importer)
        assert BankStatementImport.query.count()==BankTransaction.query.count()==FiscalYear.query.count()==0
        imported=import_data(data,importer)
        assert imported.new_count==2 and BankTransaction.query.count()==2
