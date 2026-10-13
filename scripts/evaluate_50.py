"""Measure exact-match field accuracy on the synthetic 50-image benchmark.

Call from project root: python -m scripts.evaluate_50
Requires Tesseract and zxing-cpp installed; uses actual OCR and barcode decoding.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from app.advanced import inspect_advanced

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'sample_data' / 'benchmark_50'


def evaluate():
    truth = list(csv.DictReader((DATA / 'ground_truth.csv').open(encoding='utf-8')))
    rows = []
    correct_fields = total_fields = correct_status = verified = 0
    for item in truth:
        pred = inspect_advanced(str(DATA / item['filename']))
        matches = {}
        for field in ('product_code', 'batch', 'expiry'):
            expected = (item[field] or '').strip().upper()
            actual = (pred.get(field) or '').strip().upper()
            matches[field] = actual == expected
            correct_fields += matches[field]
            total_fields += 1
        expected_pass = item['expected_status'].upper() == 'PASS'
        correct_status += (bool(pred['passed']) == expected_pass)
        verified += bool(pred.get('barcode_verified'))
        rows.append({'filename':item['filename'], 'expected_status':item['expected_status'],
                     'predicted_status':'PASS' if pred['passed'] else 'REVIEW',
                     'barcode_status':pred.get('barcode_status'), 'field_matches':matches,
                     'ocr_confidence':pred.get('average_confidence'),
                     'processing_ms':pred.get('processing_ms')})
    report = {'samples':len(rows), 'field_exact_match_accuracy_percent': round(100*correct_fields/total_fields,2),
              'inspection_status_accuracy_percent':round(100*correct_status/len(rows),2),
              'barcode_verified_count':verified, 'rows':rows}
    output = ROOT / 'evaluation_results.json'
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}, indent=2))
    print(f'Full results saved: {output}')


if __name__ == '__main__':
    evaluate()
