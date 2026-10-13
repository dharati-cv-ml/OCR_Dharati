# Accuracy and barcode verification

- **Baseline:** 117 / 150 expected synthetic OCR fields exact match (78.00%).
- **Updated:** 149 / 150 expected synthetic OCR fields exact match (99.33%).
- Samples are synthetic, and improvements were tuned using these samples (not an independent evaluation).
- One unresolved product code error remains; no claim of reliable 98% real-world accuracy is appropriate.
- Strict barcode verification independently parses printed OCR and decoded barcode fields. PASS requires product/batch/expiry exact agreement; undecodable, missing, or conflicting codes get REVIEW.
- Demo payload convention `SKU:...;LOT:...;EXP:...` is not a GS1 Application Identifier parser.
- On Windows, run `python -m scripts.evaluate_50` to generate `evaluation_results.json` with end-to-end outcomes, after installing dependencies.
- The automated comparison rules pass unit tests, but ZXing-C++ decoding was not available in this build environment.
