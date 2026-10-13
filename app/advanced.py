"""Local image analysis helpers. Optional OpenCV and zxing-cpp enhance functionality."""
from __future__ import annotations
import time
from pathlib import Path
from PIL import Image, ImageOps
import pytesseract
from pytesseract import Output
from app.desktop import scan_file


def ocr_details(path: str) -> dict:
    """Get OCR word boxes/confidence and elapsed time; confidence is not a calibrated probability."""
    start = time.perf_counter()
    with Image.open(path) as im:
        gray = ImageOps.autocontrast(ImageOps.grayscale(ImageOps.exif_transpose(im)))
        words = pytesseract.image_to_data(gray, config='--psm 3', output_type=Output.DICT)
        boxes = []
        for i, raw in enumerate(words['text']):
            word = raw.strip()
            try:
                conf = float(words['conf'][i])
            except (TypeError, ValueError):
                continue
            if word and conf >= 0:
                boxes.append({'text':word,'confidence':round(conf,1),'x':int(words['left'][i]),'y':int(words['top'][i]),'w':int(words['width'][i]),'h':int(words['height'][i])})
        dimensions = gray.size
    return {'boxes':boxes, 'average_confidence':round(sum(b['confidence'] for b in boxes)/len(boxes),1) if boxes else None,
            'image_size':dimensions, 'ocr_details_ms':round((time.perf_counter()-start)*1000,1)}


def read_codes(path: str) -> list[dict]:
    """Decode QR and Data Matrix with zxing-cpp; returns [] if nothing detected."""
    import zxingcpp
    with Image.open(path) as im:
        img = ImageOps.exif_transpose(im).convert('RGB')
        results = zxingcpp.read_barcodes(img)
        if not results:
            results = zxingcpp.read_barcodes(ImageOps.autocontrast(ImageOps.grayscale(img)))
    output = []
    for code in results:
        pos = getattr(code, 'position', None)
        points = []
        if pos is not None:
            for name in ('top_left', 'top_right', 'bottom_right', 'bottom_left'):
                point = getattr(pos, name, None)
                if point is not None:
                    points.append([int(point.x), int(point.y)])
        output.append({'format':str(code.format), 'text':str(code.text), 'position':points})
    return output


def inspect_advanced(path: str) -> dict:
    start = time.perf_counter()
    record = scan_file(path)
    details = ocr_details(path)
    record.update(details)
    try:
        record['barcodes'] = read_codes(path)
        record['barcode_error'] = None
    except ImportError:
        record['barcodes'] = []
        record['barcode_error'] = 'zxing-cpp not installed; barcode decoding unavailable'
    except Exception as exc:
        record['barcodes'] = []
        record['barcode_error'] = f'Barcode decoding failed: {exc}'
    record['processing_ms'] = round((time.perf_counter()-start)*1000,1)
    from app.verification import verify_barcode_ocr
    return verify_barcode_ocr(record)


def summarize(records: list[dict]) -> dict:
    total = len(records)
    times = [r['processing_ms'] for r in records if isinstance(r.get('processing_ms'), (int,float))]
    return {'total':total,'passed':sum(bool(r.get('passed')) for r in records),
            'needs_review':sum(not r.get('passed') for r in records),
            'pass_rate':round(100*sum(bool(r.get('passed')) for r in records)/total,1) if total else 0,
            'mean_processing_ms':round(sum(times)/len(times),1) if times else None,
            'codes_found':sum(len(r.get('barcodes',[])) for r in records),
            'review_reasons': {status: sum(r.get('barcode_status') == status for r in records)
                               for status in sorted({r.get('barcode_status') for r in records if r.get('barcode_status')})}}
