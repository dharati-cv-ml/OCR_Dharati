import pytest
from app.track_trace import parse_gs1, check_gs1_against_print, save_inspection, register_unit, aggregate_units, children_of

def test_gs1_parenthesized_and_scanner():
    expected={'gtin':'09506000134352','expiry_yymmdd':'281231','lot':'L1','serial':'S1'}
    assert parse_gs1('(01)09506000134352(17)281231(10)L1(21)S1') == expected
    assert parse_gs1(']d201095060001343521728123110L1\x1d21S1') == expected

def test_gs1_rejects_invalid():
    with pytest.raises(ValueError):parse_gs1('(01)123(17)281231')

def test_print_compare():
    gs=parse_gs1('(01)09506000134352(17)281231(10)L1')
    result=check_gs1_against_print(gs, {'gtin':'09506000134352','batch':'DIFFERENT','expiry':'2028-12'})
    assert result['gtin']=='MATCH' and result['lot']=='MISMATCH' and result['expiry']=='MATCH'
    assert result['serial']=='NOT_VERIFIED'

def test_sqlite_history_and_aggregation(tmp_path):
    db=tmp_path/'local.sqlite'
    assert save_inspection(db,{'filename':'sample.png','passed':False,'processing_ms':12})==1
    for serial in ('CASE1','A','B'):register_unit(db,serial,'01234567890128')
    aggregate_units(db,'CASE1',['A','B'])
    assert children_of(db,'CASE1')==['A','B']
    with pytest.raises(ValueError):aggregate_units(db,'A',['CASE1'])
    with pytest.raises(ValueError):aggregate_units(db,'CASE1',['B'])

def test_gs1_verification_never_assumes_sku_equals_gtin():
    from app.verification import verify_barcode_ocr
    record={'passed':True,'warnings':[],'product_code':'09506000134352', 'batch':'L1','expiry':'2028-12',
            'barcodes':[{'format':'Data Matrix','text':'(01)09506000134352(17)281231(10)L1(21)SER1'}]}
    result=verify_barcode_ocr(record)
    assert result['passed'] is False
    assert result['barcode_status']=='MISSING_PRINTED_FIELD'
    assert result['gs1_comparison']['gtin']=='NOT_VERIFIED'
