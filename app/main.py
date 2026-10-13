from __future__ import annotations
import io
import re
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
import pytesseract
from pydantic import BaseModel

app = FastAPI(title="Industrial OCR Inspection API", version="1.0.0")
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 15_000_000

class Inspection(BaseModel):
    filename: str
    extracted_text: str
    product_code: str | None
    batch: str | None
    expiry: str | None
    fields_found: int
    passed: bool
    warnings: list[str]


def parse_fields(text: str) -> tuple[str | None, str | None, str | None]:
    """Read printed fields with optional/damaged separators; never use barcode as OCR.

    OCR may render ':' as '.', '^', '=', '|' or omit it entirely.
    Anchor extraction to field labels and line boundaries to avoid swallowing
    neighboring values or mistaking warning/disclaimer text for a field.
    """
    aliases = {
        'product_code': r'(?:SKU|PRODUCT\s*(?:CODE|ID)?|GTIN)',
        'batch': r'(?:LOT|BATCH|BATCH\s*(?:NO|NUMBER)?)',
        'expiry': r'(?:EXP|EXPIRY|EXPIRES|EXP\s*DATE)',
    }
    values = {}
    for raw_line in text.upper().splitlines():
        line = re.sub(r'[\u200b\u200e\u200f]', '', raw_line).strip()
        for key, name in aliases.items():
            if key in values:
                continue
            # Label must be at start or after a clear delimiter/space.
            m = re.search(r'(?<![A-Z0-9])' + name + r'\b\s*(?:[:：#=^|;.,_-]\s*){0,3}(.*)$', line)
            if not m:
                continue
            remainder = m.group(1).strip()
            if key == 'expiry':
                val = re.search(r'(?<!\d)(20\d{2})\s*[-/.]\s*(0?[1-9]|1[0-2])(?:\s*[-/.]\s*([0-3]?\d))?(?!\d)',remainder)
                if val:
                    yy, mm, dd = val.groups()
                    values[key] = f'{yy}-{int(mm):02d}' + (f'-{int(dd):02d}' if dd else '')
            else:
                val = re.match(r'([A-Z0-9][A-Z0-9-]{2,23})\b', remainder)
                if val:
                    candidate=val.group(1)
                    if candidate not in {'NOT','NONE','MISSING','DATE'}:
                        values[key] = candidate
    return (values.get('product_code'), values.get('batch'), values.get('expiry'))

def process_image(image: Image.Image, filename: str) -> Inspection:
    image = ImageOps.exif_transpose(image).convert("RGB")
    if image.width * image.height > MAX_PIXELS:
        raise HTTPException(413, "Image pixel limit exceeded")
    grayscale = ImageOps.autocontrast(ImageOps.grayscale(image))
    text = pytesseract.image_to_string(grayscale, config="--psm 6").strip()
    product_code, batch, expiry = parse_fields(text)
    fields = [product_code, batch, expiry]
    missing = [label for label, value in zip(("product_code", "batch", "expiry"), fields) if not value]
    return Inspection(filename=filename, extracted_text=text, product_code=product_code,
                      batch=batch, expiry=expiry, fields_found=3-len(missing),
                      passed=not missing, warnings=[f"Missing {label}" for label in missing])

@app.get("/health")
def health():
    return {"status": "ok", "ocr_backend": "tesseract"}

@app.post("/inspect", response_model=Inspection)
async def inspect(file: UploadFile = File(...)):
    if file.content_type not in ("image/png", "image/jpeg", "image/webp"):
        raise HTTPException(415, "Upload a PNG, JPEG or WEBP image")
    payload = await file.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise HTTPException(413, "Maximum upload size is 8 MB")
    try:
        image = Image.open(io.BytesIO(payload))
        image.verify()
        image = Image.open(io.BytesIO(payload))
        return process_image(image, file.filename or "upload")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "Invalid or unreadable image")
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(503, "Tesseract executable is not installed")
