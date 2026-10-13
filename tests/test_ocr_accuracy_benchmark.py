from scripts.evaluate_ocr_accuracy import DATA, FIELDS
from app.field_normalization import normalize_sample_fields

def test_benchmark_manifest_contains_50_images():
    import csv
    with (DATA / 'ground_truth.csv').open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==50
    assert all((DATA/row['filename']).exists() for row in rows)
    assert len(FIELDS)==3

def test_schema_normalization_not_used_for_arbitrary_identifiers():
    assert normalize_sample_fields('ABCD-1234','LOTX','2027-02') == ('ABCD-1234','LOTX','2027-02')
