# Track & Trace verification update

- Supports documented **synthetic demo** payload styles `SKU:CODE;LOT:BATCH;EXP:YYYY-MM` and `SKU^CODE_LOT^BATCH_EXP^YYYY-MM` in addition to the existing independent GS1 route.
- Reports `MISSING_PRINTED_FIELD`, `MISSING_BARCODE_FIELD`, `MISMATCH`, `CONFLICTING_BARCODES`, or `MATCH` rather than conflating missing printed data with wrong barcode contents.
- Does **not** autofill a missing printed field from a barcode. Defective labels remain REVIEW.
- Use `python -m scripts.evaluate_track_trace` to compare inspection decisions with `sample_data/benchmark_50/ground_truth.csv` on the *current machine*.
- Accuracy and PASS rate are separate metrics. A synthetically measured result is not validated production accuracy.
- Original GS1 parsing stays in `app.track_trace`; synthetic SKU identifiers are not GTINs.
- Run with `python -m app.desktop` after installing `desktop_requirements.txt`.
