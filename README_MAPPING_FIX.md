# OCR punctuation and barcode mapping fix

The OCR field parser accepts `SKU: VALUE`, `SKU VALUE`, `SKU^VALUE`, `SKU = VALUE` and similar forms without requiring perfect colon detection. Barcode parsing remains independent; mismatch values are never overwritten with encoded values.

The GS1 verifier compares fields only where the printed and encoded identifiers represent the same item (GTIN is **not** SKU). Missing independently printed fields cause REVIEW. The ZXing decoder makes a grayscale retry when its initial attempt returns no symbols. Barcode decoding should be validated on Windows with `zxing-cpp` installed.

Run with `python -m app.desktop`; evaluate with `python -m scripts.evaluate_track_trace`. For the 50 sample images expected valid/invalid status is 40/10; pass counts alone are not accuracy. This is not GMP-validated software.
