"""Optional schema-aware normalization for the synthetic demonstration label format.

Do not use this format to validate arbitrary pharmaceutical packaging or GS1 IDs.
"""
import re

def normalize_sample_fields(product, batch, expiry):
    """Correct OCR confusion ONLY when identifiers match known demo PRD/B formats."""
    if product and product.startswith('PRD'):
        suffix = product[3:].replace('O', '0').replace('I','1').replace('L','1')
        if re.fullmatch(r'[0-9S]{6,10}', suffix):
            digits = suffix.replace('S','5')
            if len(digits) == 6 or (len(digits) > 6 and digits.startswith('0') and int(digits) < 1000000):
                product = 'PRD' + digits.zfill(6)[-6:]
    if batch and batch.startswith('B'):
        suffix = batch[1:].replace('O','0').replace('I','1').replace('L','1')
        if re.fullmatch(r'[0-9S]{5,10}', suffix):
            digits = suffix.replace('S','5')
            if len(digits) == 5 or (len(digits) > 5 and digits.startswith('0') and int(digits) < 100000):
                batch = 'B' + digits.zfill(5)[-5:]
    return product, batch, expiry
