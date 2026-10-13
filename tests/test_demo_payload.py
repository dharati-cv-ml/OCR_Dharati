from app.payload_parser import parse_demo_payload
from app.verification import verify_barcode_ocr

BASE = {'product_code':'PRD000050', 'batch':'B00050', 'expiry':'2029-03', 'passed':True, 'warnings':[]}

def test_synthetic_colon_and_semicolon():
    assert parse_demo_payload('SKU:PRD000050;LOT:B00050;EXP:2029-03') == {'product_code':'PRD000050','batch':'B00050','expiry':'2029-03'}

def test_synthetic_caret_underscore():
    assert parse_demo_payload('SKU^PRD000050_LOT^B00050_EXP^2029-03') == {'product_code':'PRD000050','batch':'B00050','expiry':'2029-03'}

def test_matching():
    data={**BASE,'barcodes':[{'text':'SKU^PRD000050_LOT^B00050_EXP^2029-03'}]}
    result=verify_barcode_ocr(data)
    assert result['passed'] and result['barcode_status']=='MATCH'

def test_missing_printed_expiry():
    data={**BASE,'expiry':None,'passed':False,'barcodes':[{'text':'SKU^PRD000050_LOT^B00050_EXP^2029-03'}]}
    result=verify_barcode_ocr(data)
    assert not result['passed'] and result['barcode_status']=='MISSING_PRINTED_FIELD'
    assert result['field_comparison']['expiry']['status']=='MISSING_PRINTED_EXPIRY'

def test_actual_mismatch():
    data={**BASE,'batch':'B00051','barcodes':[{'text':'SKU:PRD000050;LOT:B00050;EXP:2029-03'}]}
    result=verify_barcode_ocr(data)
    assert not result['passed'] and result['barcode_status']=='MISMATCH'

def test_conflict():
    data={**BASE,'barcodes':[{'text':'SKU^PRD000050_LOT^B00050_EXP^2029-03'}, {'text':'SKU^PRD000050_LOT^B00051_EXP^2029-03'}]}
    assert verify_barcode_ocr(data)['barcode_status']=='CONFLICTING_BARCODES'
