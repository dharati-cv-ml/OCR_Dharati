"""Demonstrate GS1 decoding, local inspection ledger and parent-child aggregation."""
from pathlib import Path
from app.track_trace import parse_gs1, check_gs1_against_print, save_inspection, register_unit, aggregate_units, children_of

DB = Path('track_trace_demo.sqlite3')
if DB.exists():
    raise SystemExit('track_trace_demo.sqlite3 already exists. Rename or delete it to rerun the fresh demo.')
code = '(01)09506000134352(17)281231(10)LOT902(21)SERIAL001'
parsed = parse_gs1(code)
comparison = check_gs1_against_print(parsed, {'gtin':'09506000134352', 'batch':'LOT902', 'expiry':'2028-12', 'serial':'SERIAL001'})
print('GS1 decoded:', parsed)
print('Printed-versus-code:', comparison)
save_inspection(DB, {'filename':'synthetic_gs1.png','passed':all(v=='MATCH' for v in comparison.values()),'processing_ms':None,'comparison':comparison})
for serial in ('CASE-1','SERIAL001','SERIAL002'):
    register_unit(DB, serial, '09506000134352', 'LOT902')
aggregate_units(DB, 'CASE-1', ['SERIAL001', 'SERIAL002'])
print('Case children:', children_of(DB,'CASE-1'))
print('Evidence saved:', DB.resolve())
