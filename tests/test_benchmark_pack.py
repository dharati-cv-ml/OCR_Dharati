from pathlib import Path
import csv


def test_benchmark_pack_has_50_distinct_images():
    folder = Path(__file__).resolve().parents[1] / 'sample_data' / 'benchmark_50'
    images = list(folder.glob('*.png'))
    assert len(images) == 50
    assert len({p.name for p in images}) == 50
    with (folder / 'ground_truth.csv').open(newline='', encoding='utf-8') as f:
        records = list(csv.DictReader(f))
    assert len(records) == 50
    assert sum(r['symbology'] == 'QR' for r in records) == 25
    assert sum(r['symbology'] == 'Data Matrix' for r in records) == 25
    assert sum(r['expected_status'] == 'REVIEW' for r in records) == 10
