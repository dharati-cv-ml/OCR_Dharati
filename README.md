> **Demo benchmark:** 149/150 synthetic OCR fields matched ground truth after schema-aware corrections (99.33%). This is in-sample, not production accuracy. Barcode decoder and camera require testing on Windows.

# Industrial OCR Inspection API

A working FastAPI prototype for text inspection on **synthetic** pharmaceutical-style carton labels. Uses local Tesseract OCR, extracts SKU, batch and expiry, and reports missing fields. No employer code or private datasets are included.

> **Scope:** This is an engineering demo, not a validated pharmaceutical quality-control system. There is no Data Matrix decoding, defect detection, regulatory validation, or measured production accuracy claim.

## Quick start (Python 3.11+)

Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and ensure `tesseract` is on PATH. In this repository:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` and POST `sample_data/carton.png` to `/inspect`.

```bash
curl -F "file=@sample_data/carton.png;type=image/png" http://localhost:8000/inspect
```

## Docker

```bash
docker build -t industrial-ocr .
docker run --rm -p 8000:8000 industrial-ocr
```

## Tests

```bash
pytest -q
```

## Architecture

`Upload -> MIME/size/image checks -> EXIF normalization -> grayscale/autocontrast -> Tesseract -> regex fields -> JSON result`

## Tradeoffs / next engineering milestones

- Current OCR uses Tesseract `--psm 6`; real manufacturing camera images require ROI detection, illumination normalization and controlled benchmarking.
- Regex extraction expects explicitly labelled fields and ISO-style expiry; date validation and other label formats are future work.
- Benchmark on a public or self-created, licensed holdout set before reporting accuracy/latency.
- Add Data Matrix detection and structured validation only once you have a compliant test dataset.
- GitHub Actions runs tests and a Docker build on pushes and PRs.

## Legal / attribution

All demo label data are synthetic. Project code is original for this example and may be adapted. Tesseract is an independent OCR engine with its own license. MIT project license applies to this repo's own source code only.
