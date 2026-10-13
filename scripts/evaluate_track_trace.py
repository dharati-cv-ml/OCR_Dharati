"""Full pipeline benchmark, requires Tesseract and zxing-cpp installed."""
from __future__ import annotations
import csv, json
from pathlib import Path
from app.advanced import inspect_advanced

ROOT = Path(__file__).resolve().parents[1]

def main():
    base = ROOT / 'sample_data' / 'benchmark_50'
    with (base / 'ground_truth.csv').open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    detailed=[]
    for row in rows:
        result=inspect_advanced(str(base / row['filename']))
        expected=row['expected_status']
        predicted='PASS' if result['passed'] else 'REVIEW'
        detailed.append({'filename':row['filename'],'expected':expected,'predicted':predicted,
                         'correct':expected == predicted,'barcode_status':result.get('barcode_status'),
                         'observed_fields':{k:result.get(k) for k in ('product_code','batch','expiry')},
                         'expected_fields':{k:row.get(k) for k in ('product_code','batch','expiry')},
                         'field_comparison':result.get('field_comparison')})
    correct=sum(r['correct'] for r in detailed)
    report={'images':len(rows),'correct_decisions':correct,'decision_accuracy_percent':round(100*correct/len(rows),2),
            'expected_passes':sum(r['expected']=='PASS' for r in detailed),
            'actual_passes':sum(r['predicted']=='PASS' for r in detailed),
            'rows':detailed}
    output=ROOT/'track_trace_evaluation.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"{correct}/{len(rows)} decisions correct ({report['decision_accuracy_percent']}%); result: {output}")
    for r in detailed:
        if not r['correct']:
            print('WRONG:',r['filename'],r['expected'],r['predicted'],r['barcode_status'])

if __name__=='__main__':main()
