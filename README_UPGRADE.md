# VisionInspect Pro — Desktop Upgrade

All processing is local. No browser or HTTP endpoint is necessary for desktop usage.

## Features
- Capture still images from webcam 0 and inspect them (requires camera access)
- OCR words with Tesseract-provided confidence and preview bounding boxes
- QR and Data Matrix decoding using zxing-cpp
- Processing duration in milliseconds (not guaranteed real-time performance)
- Inspection analytics dialog (total, pass rate, average duration, codes)
- CSV and JSON export, batch folder inspection, existing OCR field extraction

## Windows VS Code / PowerShell

Extract the ZIP, open `visioninspect-pro` folder and open a terminal:

```powershell
cd D:\visioninspect-pro
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop_requirements.txt
.\.venv\Scripts\python.exe -m app.desktop
```

If `zxing-cpp` or OpenCV is unavailable for your Python version, install Python 3.11 and recreate `.venv` with `py -3.11 -m venv .venv`.

Install Tesseract OCR separately. If Tesseract is in `C:\Program Files\Tesseract-OCR`, the application automatically discovers it. The other dependencies are listed in `desktop_requirements.txt`.

## Operation
1. Select an image or open Camera; click Capture & inspect.
2. Inspect shows extracted fields, Tesseract word confidence, total processing time and QR/Data Matrix results.
3. Toggle word bounding boxes under the preview.
4. Open Analytics for aggregate inspection metrics.
5. Export CSV/JSON to keep results.

**Notes:** Tesseract confidence is a per-word OCR score (not calibrated correctness). `PASS` only means required text fields were parsed; it does not validate printed text against reference data or expiry rules. Camera preview itself is live, but OCR runs on still captures. Timing is per-image wall-clock time and depends on your hardware. For a production packaging inspection system, add reference-data validation, rigorous labeled-set evaluation, and industrial-camera integration.

## Preview fix and 50-image benchmark pack

The desktop preview now uses a persistent Tk image widget instead of a canvas image. It displays the selected file and overlays **green OCR word rectangles** when `Show OCR bounding boxes` is enabled. Decoded barcode location outlines display **amber** when `zxing-cpp` provides corner positions.

Open **Select image** and choose a PNG in `sample_data/benchmark_50`, then click **Inspect image**. Alternatively use **Scan folder** on `sample_data/benchmark_50`; this will run 50 inspections, which may take time. These are **synthetic** test images, not a calibrated industrial inspection dataset.

* 25 QR images and 25 Data Matrix images with different sample product/batch/expiry values.
* 40 complete labels; 10 deliberately omit an expiry field to test the Needs Review state.
* `ground_truth.csv` contains the expected fields and barcode payloads. Recognition may be imperfect (notably O/0), so compare predictions to ground truth; don't treat the detection count as an accuracy measurement.
* **Green boxes = OCR text regions; amber outlines = decoded 2D symbol locations.** QR/Data Matrix is decoded by the optional `zxing-cpp` dependency. If the status says decoder unavailable, install the dependencies from `desktop_requirements.txt`.
* For these generated samples, text rectangles are drawn only **after inspection**, not merely when loading an image.

Run from the extracted project root in VS Code PowerShell:

```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop_requirements.txt
.\.venv\Scripts\python.exe -m app.desktop
```

If your `.venv` already exists, skip creation. If the Python 3.14 installation fails due to dependency wheels, use Python 3.11 instead. The webcam and zxing-cpp decoding must be verified locally on Windows.

## Barcode-to-print verification & measured accuracy

This version adds **strict** comparison of SKU/product code, LOT/batch and EXP/expiry
from OCR and QR/Data Matrix. An image PASSES only when all three printed fields are
present, a code can be decoded, the payload includes all three fields, and values match.
When the barcode is missing, undecodable, conflicting, or mismatched, status is REVIEW.
Barcode data is **not** substituted for OCR data during comparison.

The included synthetic images use the payload convention
`SKU:PRD000001;LOT:B00001;EXP:2028-02`. Real GS1 DataMatrix needs its own
Application Identifier (AI) parser and validation; this project does not yet implement GS1.

Run a 50-image test from the project root (with dependencies and Tesseract installed):

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_50
```

This saves `evaluation_results.json` containing per-image outcomes and separate:
- **Field exact-match accuracy** (all 150 expected fields, including missing fields)
- **Inspection status accuracy** (PASS/REVIEW vs labeled expectation)
- **Barcode verification count**

**OCR confidence is not accuracy.** The original reported industrial CNN accuracy
of 98% cannot be assigned to this Tesseract-based prototype. Even 98% measured on
these synthetic images would not validate real-world pharmaceutical production.

### Measured local OCR baseline and improvement (synthetic benchmark only)

This update was evaluated using the installed Tesseract engine against the included
`ground_truth.csv` (50 images × 3 fields = 150 labeled fields):

- Previous baseline (PSM 6, without normalization): **117/150 = 78.00%** exact matches.
- Updated demo-schema parser with conditional alternate PSM: **149/150 = 99.33%** exact matches.
- Remaining incorrect result: package_03_qr.png product code, digit 3 incorrectly read as 5.

This is **not** a held-out dataset and the changes were developed using these same images;
therefore the 99.33% result must not be used as a generalization or production accuracy claim.
Use an independent real-world dataset to evaluate before making external claims.
The evaluation command creates an updated `evaluation_results.json` on your PC; barcode
verification counts were not measured in this environment because ZXing-C++ was not installed.

## CV-aligned Track & Trace extension (October 2026)

This open-source **reconstruction/demo**, not former employer proprietary software, adds:
- `app/track_trace.py`: GS1 subset decoder for AIs `01` GTIN, `17` expiry, `10` lot, `21` serial; accepts parenthesized demonstration syntax and FNC1 group-separator scans.
- Strict comparison of printed GTIN/lot/expiry/serial to encoded fields. Unobserved fields are **NOT_VERIFIED**, never silently presumed correct.
- SQLite evidence ledger, serialized units, and parent-child aggregation with duplicate/reparent/cycle rejection.
- `python -m scripts.track_trace_demo`: generates a local demonstration database and shows parent-child membership.
- `pytest -q`: new tests of the GS1 parsing, comparison and ledger.

**Remaining gaps relative to historical CV:** the desktop UI currently uses Tesseract, not a custom trained CNN. Its 700+ ms example is not a sub-3 ms ONNX/TensorRT inference benchmark. Camera is a webcam still capture, not synchronized industrial cameras. SQLite is a local prototype, not PLC/line-controller integration. Dataset metrics are from synthetic, non-held-out labels. The CV's historical 98% and sub-3 ms figures are historical BLUIE claims and **are not results of this repository**. The GS1 parser is a limited subset, not a complete GS1 General Specifications implementation or regulatory validation.
