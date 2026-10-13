"""Image-based benchmark with separate OCR, decode, decision metrics and stage latency.
Run: python -m scripts.generate_robust_dataset && python -m scripts.evaluate_robust
"""
from __future__ import annotations
import csv,json,statistics,time,math,argparse
from pathlib import Path
from app.desktop import scan_file,find_tesseract
from app.advanced import ocr_details,read_codes
from app.verification import verify_barcode_ocr
from app.track_trace import register_unit
from tempfile import TemporaryDirectory
import pytesseract
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'sample_data'/'robust_250'
KEYS=('product_code','batch','expiry')

def pct(n,d):return round(100*n/d,2) if d else None
def stage_stats(vals):
    if not vals:return {'n':0,'mean_ms':None,'median_ms':None,'p95_ms':None}
    ordered=sorted(vals);return {'n':len(vals),'mean_ms':round(statistics.mean(vals),2),
        'median_ms':round(statistics.median(vals),2),'p95_ms':round(ordered[math.ceil(.95*len(ordered))-1],2)}

def serial_checks():
    with TemporaryDirectory() as td:
        db=Path(td)/'serials.sqlite'; detected=0; total=20
        for i in range(total):
            serial=f'SYNTH-SERIAL-{i:05d}'
            register_unit(db,serial,'09506000134352')
            try: register_unit(db,serial,'09506000134352')
            except __import__('sqlite3').IntegrityError: detected+=1
    return {'duplicate_attempts':total,'duplicates_rejected':detected,'note':'Database-only duplicate registration checks, not image-based serial OCR'}

def evaluate(limit=None):
    tess=find_tesseract()
    if tess:pytesseract.pytesseract.tesseract_cmd=tess
    if not (DATA/'ground_truth.csv').exists():raise SystemExit('Generate dataset first: python -m scripts.generate_robust_dataset')
    with (DATA/'ground_truth.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if limit:rows=rows[:limit]
    details=[];timings={k:[] for k in ('ocr_ms','ocr_boxes_ms','barcode_ms','verification_ms','total_ms')};decode_available=True
    for index,row in enumerate(rows,1):
        path=str(DATA/row['filename']);t0=time.perf_counter();t=time.perf_counter()
        record=scan_file(path);timings['ocr_ms'].append((time.perf_counter()-t)*1000)
        t=time.perf_counter();boxes=ocr_details(path);timings['ocr_boxes_ms'].append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        try:
            codes=read_codes(path);decode_error=None
        except (ImportError, OSError) as exc:
            codes=[];decode_error=f'Decoder unavailable: {exc}';decode_available=False
        except Exception as exc:
            codes=[];decode_error=f'Decoder exception: {exc}'
        timings['barcode_ms'].append((time.perf_counter()-t)*1000)
        record.update(boxes);record['barcodes']=codes;record['barcode_error']=decode_error
        t=time.perf_counter();verified=verify_barcode_ocr(record);timings['verification_ms'].append((time.perf_counter()-t)*1000)
        timings['total_ms'].append((time.perf_counter()-t0)*1000)
        observation={k:verified.get(k) for k in KEYS}
        expect={k:row['printed_'+k] for k in KEYS}
        correct_fields={k: (observation[k] or '') == (expect[k] or '') for k in KEYS}
        prediction='PASS' if verified['passed'] else 'REVIEW'
        details.append({'filename':row['filename'],'variant':row['variant'],'expected_decision':row['expected_status'],
          'predicted_decision':prediction,'correct_decision':prediction==row['expected_status'],
          'printed_truth':expect,'ocr_observed':observation,'field_correct':correct_fields,
          'barcode_status':verified.get('barcode_status'), 'decoded_count':len(codes),
          'decoded_payloads':[c['text'] for c in codes], 'barcode_error':decode_error,
          'warnings':verified.get('warnings',[]), 'total_ms':round(timings['total_ms'][-1],2)})
        if index%25==0:print(f'Processed {index}/{len(rows)}')
    count=len(details)
    metric={k:{'correct':sum(d['field_correct'][k] for d in details),'total':count,'accuracy_percent':pct(sum(d['field_correct'][k] for d in details),count)} for k in KEYS}
    variants=sorted({r['variant'] for r in details})
    summary={'dataset': '250 transformations of original 50 synthetic label images; NOT independent real-world photographs',
       'images':count,'expected_passes':sum(d['expected_decision']=='PASS' for d in details),
       'predicted_passes':sum(d['predicted_decision']=='PASS' for d in details),
       'decision_accuracy_percent':pct(sum(d['correct_decision'] for d in details),count) if decode_available else None,
       'decision_metric_valid':decode_available,
       'decision_metric_note':('End-to-end decision accuracy is unavailable because the barcode decoder is missing; do not interpret review-only outcomes as pipeline performance.' if not decode_available else 'Measured on synthetic augmentations, not real industrial imagery.'),
       'false_accepts':sum(d['predicted_decision']=='PASS' and d['expected_decision']=='REVIEW' for d in details),
       'false_rejects':sum(d['predicted_decision']=='REVIEW' and d['expected_decision']=='PASS' for d in details),
       'ocr_field_metrics':metric,
       'barcode':{'decoder_available_for_all':decode_available,'images_with_decoded_codes':sum(d['decoded_count']>0 for d in details),
         'decode_rate_percent':pct(sum(d['decoded_count']>0 for d in details),count),
         'unavailable_or_error_count':sum(bool(d['barcode_error']) for d in details),
         'matching_payloads':sum(d['barcode_status']=='MATCH' for d in details),
         'note':'Decode rate is not barcode field accuracy; compare decoded payloads with independent ground truth.'},
       'variants':{v:{'images':sum(d['variant']==v for d in details),
                   'decision_accuracy_percent':pct(sum(d['correct_decision'] for d in details if d['variant']==v),sum(d['variant']==v for d in details))} for v in variants},
       'latency':{k:stage_stats(v) for k,v in timings.items()},'duplicate_serials':serial_checks(), 'records':details}
    output=ROOT/'robust_evaluation.json';output.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(f"Decision accuracy: {summary['decision_accuracy_percent']}%, false accepts: {summary['false_accepts']}, false rejects: {summary['false_rejects']}")
    print(f"OCR field accuracy: {[ (k,v['accuracy_percent']) for k,v in metric.items() ]}")
    print(f"Barcode decode rate: {summary['barcode']['decode_rate_percent']}%; total p95 {summary['latency']['total_ms']['p95_ms']} ms")
    print(f'Report: {output}')
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=None);args=p.parse_args();evaluate(limit=args.limit)
