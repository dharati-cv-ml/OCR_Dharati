"""Compare independent printed OCR fields with machine-readable barcode data.

Missing or undecodable barcodes never count as verified matches. This is intentionally
strict, suitable for a review-oriented demonstration, not a validated GMP system.
"""
from __future__ import annotations
from app.main import parse_fields
from app.payload_parser import parse_demo_payload

FIELDS = ('product_code', 'batch', 'expiry')


def verify_barcode_ocr(record: dict) -> dict:
    codes = record.get('barcodes') or []
    result = dict(record)
    result['barcode_verified'] = False
    result['barcode_status'] = 'NO_BARCODE'
    result['field_comparison'] = {}
    warnings = list(result.get('warnings') or [])
    if result.get('barcode_error'):
        result['barcode_status'] = 'DECODER_UNAVAILABLE'
        warnings.append(result['barcode_error'])
    elif not codes:
        warnings.append('No readable QR/Data Matrix; comparison not possible')
    else:
        # GS1-coded serials require GS1 AI decoding; SKU is not interchangeable with GTIN.
        gs1_codes = [c for c in codes if '(01)' in c.get('text','') or c.get('text','').startswith(']d2')]
        if gs1_codes:
            from app.track_trace import parse_gs1, check_gs1_against_print
            try:
                payloads = [parse_gs1(c['text']) for c in gs1_codes]
                if any(p != payloads[0] for p in payloads[1:]):
                    result['barcode_status'] = 'CONFLICTING_BARCODES'
                    warnings.append('Conflicting GS1 codes')
                else:
                    gs1 = payloads[0]
                    # GTIN != product SKU. Only compare semantically matching printed fields.
                    comparisons = {}
                    candidates = [('gtin', 'gtin'), ('lot','batch'), ('serial','serial')]
                    for encoded_key, printed_key in candidates:
                        encoded = gs1.get(encoded_key)
                        if not encoded:
                            continue
                        printed = result.get(printed_key)
                        comparisons[encoded_key] = {
                            'ocr': printed, 'barcode': encoded,
                            'status': 'MATCH' if printed and str(printed).upper()==str(encoded).upper()
                                      else 'MISMATCH' if printed else 'MISSING_PRINTED_FIELD'
                        }
                    if gs1.get('expiry_yymmdd'):
                        raw = gs1['expiry_yymmdd']
                        encoded_exp = f'20{raw[:2]}-{raw[2:4]}'
                        printed_exp = result.get('expiry')
                        # 00 day in GS1 represents the end of the indicated month.
                        is_match = bool(printed_exp and (printed_exp == encoded_exp or
                          (raw[4:] != '00' and printed_exp == encoded_exp+'-'+raw[4:])))
                        comparisons['expiry'] = {
                            'ocr': printed_exp, 'barcode': encoded_exp,
                            'status':'MATCH' if is_match else 'MISMATCH' if printed_exp else 'MISSING_PRINTED_FIELD'
                        }
                    result['gs1_fields'] = gs1
                    result['field_comparison'] = comparisons
                    result['gs1_comparison'] = {k: ('NOT_VERIFIED' if v['status']=='MISSING_PRINTED_FIELD' else v['status']) for k,v in comparisons.items()}
                    statuses = {v['status'] for v in comparisons.values()}
                    result['barcode_status'] = (
                        'MATCH' if statuses == {'MATCH'} else
                        'MISMATCH' if 'MISMATCH' in statuses else
                        'MISSING_PRINTED_FIELD' if 'MISSING_PRINTED_FIELD' in statuses else 'NOT_VERIFIED')
                    result['barcode_verified'] = result['barcode_status'] == 'MATCH'
                    for key, val in comparisons.items():
                        if val['status'] != 'MATCH':
                            warnings.append(f"{key}: {val['status']} (OCR={val['ocr'] or '—'}, barcode={val['barcode']})")
            except ValueError as exc:
                result['barcode_status'] = 'INVALID_GS1'
                warnings.append(str(exc))
            result['warnings'] = list(dict.fromkeys(warnings))
            result['passed'] = bool(result.get('passed') and result['barcode_verified'])
            return result
        parsed = []
        for code in codes:
            fields = parse_demo_payload(code.get('text', ''))
            if any(fields.values()):
                parsed.append(fields)
        if not parsed:
            result['barcode_status'] = 'UNSUPPORTED_PAYLOAD'
            warnings.append('Barcode payload lacks supported SKU/LOT/EXP fields')
        elif len(parsed) > 1 and any(p != parsed[0] for p in parsed[1:]):
            result['barcode_status'] = 'CONFLICTING_BARCODES'
            warnings.append('Multiple barcodes contain conflicting data')
        else:
            barcode = parsed[0]
            comparisons = {}
            for field in FIELDS:
                printed = result.get(field)
                encoded = barcode.get(field)
                comparisons[field] = {
                    'ocr': printed, 'barcode': encoded,
                    'status': 'MATCH' if printed and encoded and str(printed).upper() == str(encoded).upper()
                              else 'MISMATCH' if printed and encoded
                              else 'MISSING_PRINTED_' + field.upper() if not printed and encoded
                              else 'MISSING_BARCODE_' + field.upper() if printed and not encoded
                              else 'MISSING_BOTH',
                }
            result['field_comparison'] = comparisons
            statuses = {x['status'] for x in comparisons.values()}
            result['barcode_status'] = ('MATCH' if statuses == {'MATCH'}
                                        else 'MISMATCH' if 'MISMATCH' in statuses
                                        else 'MISSING_PRINTED_FIELD' if any(x.startswith('MISSING_PRINTED_') for x in statuses)
                                        else 'MISSING_BARCODE_FIELD' if any(x.startswith('MISSING_BARCODE_') for x in statuses)
                                        else 'NOT_VERIFIED')
            result['barcode_verified'] = result['barcode_status'] == 'MATCH'
            for field, values in comparisons.items():
                if values['status'] != 'MATCH':
                    warnings.append(f"{field}: {values['status']} (OCR={values['ocr'] or '—'}, barcode={values['barcode'] or '—'})")
    result['warnings'] = list(dict.fromkeys(warnings))
    result['passed'] = bool(result.get('passed') and result['barcode_verified'])
    return result
