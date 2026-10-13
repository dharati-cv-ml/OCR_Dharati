from app.main import parse_fields
from app.verification import verify_barcode_ocr

def test_colon_variants():
    for sample in ('SKU: PRD000050','SKU PRD000050','SKU^ PRD000050','SKU = PRD000050','SKU . PRD000050'):
        assert parse_fields(sample)[0]=='PRD000050'

def test_multiple_lines_and_missing_expiry():
    assert parse_fields('SKU PRD000050\nLOT: B00050\nEXP:')[0:2]==('PRD000050','B00050')
    assert parse_fields('SKU PRD000050\nLOT: B00050\nEXP:')[2] is None

def test_date_separator():
    assert parse_fields('EXP . 2029/3')[2]=='2029-03'

def test_demo_matching_does_not_silently_replace_bad_ocr():
    source=dict(product_code='PRD000050', batch='B00051', expiry='2029-03',passed=True,warnings=[],
        barcodes=[{'text':'SKU^PRD000050_LOT^B00050_EXP^2029-03'}])
    result=verify_barcode_ocr(source)
    assert result['barcode_status']=='MISMATCH'
    assert not result['passed']
    assert result['field_comparison']['batch']['status']=='MISMATCH'

def test_demo_missing_expiry():
    source=dict(product_code='PRD000050',batch='B00050',expiry=None,passed=False,warnings=[],
        barcodes=[{'text':'SKU^PRD000050_LOT^B00050_EXP^2029-03'}])
    result=verify_barcode_ocr(source)
    assert result['barcode_status']=='MISSING_PRINTED_FIELD'
    assert result['field_comparison']['expiry']['status']=='MISSING_PRINTED_EXPIRY'
