from app.verification import verify_barcode_ocr
BASE = dict(product_code='ABC1234', batch='ZX902', expiry='2027-12',
            passed=True, warnings=[], barcodes=[{'format':'Data Matrix', 'text':'SKU:ABC1234;LOT:ZX902;EXP:2027-12'}])

def test_matching():
    r=verify_barcode_ocr(BASE)
    assert r['passed'] and r['barcode_status']=='MATCH' and r['barcode_verified']

def test_mismatch():
    r=verify_barcode_ocr({**BASE, 'batch':'ZX903'})
    assert not r['passed'] and r['barcode_status']=='MISMATCH'
    assert r['field_comparison']['batch']['status']=='MISMATCH'

def test_missing_barcode_cannot_pass():
    r=verify_barcode_ocr({**BASE, 'barcodes':[]})
    assert not r['passed'] and r['barcode_status']=='NO_BARCODE'

def test_missing_printed_field():
    r=verify_barcode_ocr({**BASE, 'expiry':None})
    assert not r['passed'] and r['field_comparison']['expiry']['status']=='MISSING_PRINTED_EXPIRY'

def test_conflicting_codes():
    r=verify_barcode_ocr({**BASE, 'barcodes':BASE['barcodes']+[{'text':'SKU:ABC1234;LOT:DIFFERENT;EXP:2027-12'}]})
    assert not r['passed'] and r['barcode_status']=='CONFLICTING_BARCODES'
