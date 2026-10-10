"""Audit call inventory and original helper transaction-boundary probes."""
from pathlib import Path
import ast
import json
import runpy

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
calls = []
for file in sorted((ROOT / 'backend').rglob('*.py')):
    tree = ast.parse(file.read_text(encoding='utf-8-sig'))
    parents = {child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'log_audit_event':
            parent = parents.get(node)
            while parent is not None and not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parent = parents.get(parent)
            calls.append(dict(file=file.relative_to(ROOT).as_posix(), line=node.lineno,
                              function=parent.name if parent else None,
                              action=ast.unparse(node.args[0]) if node.args else None,
                              status='inventoried_not_individually_verified'))
calls.sort(key=lambda c:(c['file'],c['line']))
(OUT / 'AUDIT_CALL_INVENTORY.json').write_text(json.dumps(calls,indent=2)+'\n',encoding='utf-8')

runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.audit_event import AuditEvent, AuditAction
from backend.services.security import SecurityService

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []
for dirty, failure in [(False,False),(True,False),(True,True)]:
    with app.test_request_context('/__audit/transaction'):
        db.create_all()
        member = Member(id=1,vorname='Audit',nachname='Vorher',email='transaction@example.com',passwort_hash='unused')
        db.session.add(member); db.session.commit()
        if dirty: member.nachname = 'NochNichtFreigegeben'
        def fail(*args): raise OperationalError('synthetic audit insert',{},Exception('audit-only'))
        if failure: event.listen(AuditEvent,'before_insert',fail)
        try:
            SecurityService.log_audit_event(AuditAction.READ_SENSITIVE_SELF,'member',1,actor_id=1)
        finally:
            if failure: event.remove(AuditEvent,'before_insert',fail)
        db.session.rollback()
        db.session.remove()
        result = dict(pending_member_change=dirty, audit_insert_failure=failure,
                      name_after_outer_rollback=db.session.get(Member,1).nachname,
                      audit_count=AuditEvent.query.count())
        assert result['name_after_outer_rollback'] == ('NochNichtFreigegeben' if dirty and not failure else 'Vorher')
        assert result['audit_count'] == (0 if failure else 1)
        results.append(result)
        db.session.remove(); db.drop_all()
output = dict(date='2026-09-21',groups=3,inventory_calls=len(calls),results=results,
              limits='Original helper, SQLite memory, synthetic pending member change. Outer rollback is deliberate test action. Inventory is AST coverage only, not proof of each caller contract or product bug. No real member changes, credentials, network or production.')
(OUT / 'AUDIT_TRANSACTION_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
print(json.dumps({file:len([c for c in calls if c['file']==file]) for file in sorted({c['file'] for c in calls})},indent=2))
