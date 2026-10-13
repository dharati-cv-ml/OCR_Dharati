# What this project demonstrates vs historical BLUIE experience

This is an original, standalone portfolio reconstruction using synthetic labels and permissive third-party tools. Do not imply that it includes original BLUIE source code, training data, or proprietary system architecture.

| CV experience | Demonstration in repository | Missing for technical parity |
|---|---|---|
| Pharma OCR/OCV, 3–4 print lines | Tesseract OCR, word boxes and required-field validation | Character-level custom CNN trained on diverse real camera images |
| Barcode, QR, 2D Data Matrix | Optional ZXing decoder with printed-text cross-check | Full GS1 compliance / DPM-grade decoding validation |
| Track & Trace serialization, aggregation | GS1 AI subset parser, SQL serial ledger, parent-child relationship checks | Transactional integration with plant equipment, full hierarchy and regulatory audit controls |
| One to four synchronized cameras | Webcam still capture | Industrial multi-camera synchronization, trigger I/O, temporal alignment |
| 49% → 98% CNN accuracy | Measured synthetic field-matching benchmark for *different model* | Independent held-out real-image validation of a CNN |
| <3 ms processing | Millisecond wall-clock measurements of Tesseract | Optimized C++/ONNX/TensorRT character inference and hardware benchmark |
| C++/VB.NET/SQL production system | Python/Tk desktop and SQLite local ledger | C++/VB.NET bridges, PLC adapter, access control, production DB |
| 10,000+ inspections/day | Folder batch processing | Endurance and throughput test with production-like data |

**To discuss at interviews:** separate historical engineering contributions from this newly built demonstration. Say “I recreated selected Track & Trace concepts in a local open-source portfolio application”; do not claim this demo has the CV's previous industrial metrics.

Run desktop:
```powershell
.\\.venv\\Scripts\\python.exe -m app.desktop
```

Run the GS1/aggregation demo:
```powershell
.\\.venv\\Scripts\\python.exe -m scripts.track_trace_demo
```

Run automated tests:
```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
```

The SQLite audit database is saved locally in your Windows profile at `~/VisionInspect/inspection_history.sqlite3`. The standalone serialization demo writes `track_trace_demo.sqlite3` to the project directory.
