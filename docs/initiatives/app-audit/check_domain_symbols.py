"""Static symbol-contract audit; no app import, database or network."""
from pathlib import Path
import ast,json,re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def enum_members(file,name):
    tree=ast.parse((ROOT/file).read_text(encoding='utf-8-sig'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
    return {n.targets[0].id:ast.literal_eval(n.value) for n in cls.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
domain=(ROOT/'docs/DOMAIN.md').read_text(encoding='utf-8')
sections=[]
for m in re.finditer(r'^#{2,3} Audit-Aktionen[^\n]*\n',domain,re.M):
    tail=domain[m.end():];end=re.search(r'^#{1,3} ',tail,re.M)
    sections.append(tail[:end.start()] if end else tail)
documented=sorted(set(re.findall(r'`([A-Z][A-Z_0-9]+)`','\n'.join(sections))))
actual=enum_members('backend/models/audit_event.py','AuditAction')
references=[]
for file in sorted((ROOT/'backend').rglob('*.py')):
    tree=ast.parse(file.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='AuditAction':
            references.append({'path':file.relative_to(ROOT).as_posix(),'line':node.lineno,'symbol':node.attr,'defined':node.attr in actual})
definitions={}
for file,name in [('backend/models/member.py','Role'),('backend/models/member.py','Funktion'),('backend/models/event.py','EventType'),('backend/models/event.py','EventAudience'),('backend/models/event.py','BillPaidBy'),('backend/models/merch_order.py','OrderStatus'),('backend/models/accounting.py','FiscalYearStatus'),('backend/models/accounting.py','ClaimStatus')]:
    definitions[name]=enum_members(file,name)
result={'method':'AST enum definitions and literal AuditAction attribute references; DOMAIN audit sections only. Not runtime logging coverage, aliases/dynamic getattr excluded.',
        'audit_action_count':len(actual),'documented_audit_symbols':documented,'documented_but_undefined':sorted(set(documented)-actual.keys()),
        'defined_but_not_in_documented_examples':sorted(actual.keys()-set(documented)),
        'literal_reference_count':len(references),'undefined_literal_references':[r for r in references if not r['defined']],
        'enum_definitions':definitions}
(OUT/'DOMAIN_SYMBOL_CHECKS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('defined_but_not_in_documented_examples','enum_definitions','method')},indent=2))
