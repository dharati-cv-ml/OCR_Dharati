# Track & Trace: OCR accuracy update

This package is an update of the **Track & Trace (19-test) edition**, not the CNN comparison edition.

## Change and reproducible measurement

- Switched the initial packaging OCR pass from Tesseract **PSM 6** (single uniform block) to **PSM 3** (automatic page segmentation), which better separates the printed label from nearby QR/Data Matrix symbols on the supplied synthetic packaging images.
- Runs an optional PSM 6 secondary pass **only when a field is missing**; it does not silently replace conflicting recognized values with barcode or ground-truth values.
- Uses PSM 3 for displayed OCR bounding boxes as well.
- Adds an independent, reproducible OCR-only benchmark:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_ocr_accuracy
```

This writes `ocr_accuracy_report.json`, with expected/predicted values and exact-match results for each field and image.

On this build environment, **150/150 fields (100.00%)** matched the supplied 50 *synthetic* samples, compared with **149/150 (99.33%)** in the unmodified Track & Trace baseline. This does **not** measure true industrial/generalization accuracy; sample designs are highly repetitive, and the code includes demo-format-aware normalizations for PRD###### and B#####. Nothing in this report supports a 98% performance claim on new real photographs or sub-3 ms end-to-end performance.

## Important barcode distinction

Use the existing `python -m scripts.evaluate_50` to evaluate complete inspection including barcode decoding. An optional ZXing-C++ dependency is required; **barcode verification must not be treated as passed when the decoder is missing, payload is unsupported, or a required field is absent**. `pass/review` rates are not OCR accuracy rates.

## Next validation stage

Collect permission-cleared real packaging photographs with varied fonts, blur, lighting, orientations, and known truth labels. Split by product / acquisition session, reserve a truly unseen holdout, and report per-field exact match, character error rate, missed-field and false-accept rates and p50/p95 end-to-end latency. Evaluate Data Matrix and GS1 checks independently. Never automatically correct a printed code using decoded barcode data when assessing OCR accuracy.
