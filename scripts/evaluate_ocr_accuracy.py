"""Independent OCR-only accuracy benchmark, including deliberately missing fields.

Run: python -m scripts.evaluate_ocr_accuracy
Metrics are on synthetic generated images, not unseen industrial photographs.
Barcode decoding and PASS/REVIEW are intentionally evaluated separately.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from app.desktop import scan_file

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'sample_data' / 'benchmark_50'
FIELDS = ('product_code', 'batch', 'expiry')

def evaluate():
    truth = list(csv.DictReader((DATA / 'ground_truth.csv').open(encoding='utf-8', newline='')))
    results, counts = [], {field: 0 for field in FIELDS}
    for expected in truth:
        observed = scan_file(str(DATA / expected['filename']))
        matches = {}
        for field in FIELDS:
            truth_value = (expected[field] or '').strip().upper()
            predicted = (observed[field] or '').strip().upper()
            matches[field] = truth_value == predicted
            counts[field] += int(matches[field])
        results.append({'filename':expected['filename'],
                        'expected':{k:expected[k] for k in FIELDS},
                        'observed':{k:observed[k] for k in FIELDS},
                        'matches':matches})
    total = len(results) * len(FIELDS)
    correct = sum(counts.values())
    summary = {'dataset':'synthetic benchmark_50', 'images':len(results),
               'field_correct':correct,'field_total':total,
               'field_accuracy_percent':round(100*correct/total,2) if total else None,
               'per_field_accuracy_percent':{f:round(100*n/len(results),2) for f,n in counts.items()} if results else {}}
    report = {'summary':summary,'results':results}
    output = ROOT/'ocr_accuracy_report.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('Report:',output)
    return report

if __name__=='__main__':
    evaluate()
