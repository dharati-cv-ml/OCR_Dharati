# Robustness & Track and Trace evaluation

This version extends the original Track & Trace project with a **250-image synthetic augmented evaluation set** and separate OCR, barcode, decision and latency reporting.

## Run in Windows PowerShell (VS Code)

```powershell
.\.venv\Scripts\python.exe -m pip install -r desktop_requirements.txt
.\.venv\Scripts\python.exe -m scripts.generate_robust_dataset
.\.venv\Scripts\python.exe -m scripts.evaluate_robust
.\.venv\Scripts\python.exe -m pytest -q
```

The generated report is `robust_evaluation.json`, including per-image predictions and mismatches. No HTTP or browser needed. Original desktop launcher stays `python -m app.desktop`.

The generator creates five variants per original image: altered lighting, blur, slight rotation, wrong printed batch/expiry, and barcode occlusion. The 250 files are **transformations of 50 base synthetics**, *not* independent industrial data or proof of 98%/100% field accuracy. Barcode occlusion may not prevent decoding because of error correction; report the actual decode outcome. For the damaged-code subset we conservatively expect REVIEW, but some may decode successfully and report PASS, which will be counted as a false accept under the test's strict defect policy.

Printed-field accuracy counts missing expected fields as correctly absent. Barcode statistics report decoder availability, readable codes, and detected match status separately. **No ground-truth leakage:** expected values are used only for evaluation, not passed to OCR/barcode recognition. Duplicate serialization is tested separately via twenty attempted duplicate inserts into a temporary SQLite database; it does not imply that the image OCR system reads serial numbers.

Latency report uses wall-clock timing with mean, median, and nearest-rank p95. It records OCR, OCR boxes, barcode decoding, verification and end-to-end stages separately. Results depend on hardware, dependency versions and background load. OCR operations are separate passes; the total is not comparable to isolated CNN model inference.

**Limitations:** this is a portfolio evaluation harness, not a qualified pharmaceutical inspection system. Test independently captured and labeled real images before real-world performance claims. Some generated mismatch images use a fixed bold label style and might be harder than the original base labels. True end-to-end duplicate serial inspection requires a serial-aware barcode/OCV pipeline.
