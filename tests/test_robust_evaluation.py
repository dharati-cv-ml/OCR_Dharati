from scripts.generate_robust_dataset import generate
from scripts.evaluate_robust import stage_stats, serial_checks

def test_robust_dataset(tmp_path):
    rows=generate(out=tmp_path)
    assert len(rows)==250
    assert len(list(tmp_path.glob('*.png')))==250
    assert {r['variant'] for r in rows} == {'lighting','blur','rotation','wrong_batch','wrong_expiry','damaged_code'}
    assert all(r['expected_status']=='REVIEW' for r in rows if r['variant'] in ('wrong_batch','wrong_expiry','damaged_code'))

def test_latency_stats():
    x=stage_stats([1,2,3,4,5]);assert x['median_ms']==3 and x['p95_ms']==5

def test_duplicate_serial():
    r=serial_checks();assert r['duplicates_rejected']==20
