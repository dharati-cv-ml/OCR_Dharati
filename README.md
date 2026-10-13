# VisionInspect Pro
### Industrial OCR, OCV & Pharmaceutical Track-and-Trace Inspection

A Python-based computer vision engineering project demonstrating automated inspection of pharmaceutical-style packaging labels, optical character recognition (OCR), printed-code verification, and serialization and aggregation workflows.

The project combines a Windows desktop inspection interface, a FastAPI inspection service, structured field validation, QR/Data Matrix processing, and reproducible synthetic benchmarks.

> **Project status:** Engineering portfolio prototype. All included sample packaging data is synthetic. The application has not been validated for regulated pharmaceutical manufacturing or production-line deployment.

## Key Features

### 1. Industrial OCR and Label Inspection
- Extracts printed product information, batch identifiers, and expiry dates from pharmaceutical-style carton images.
- Uses Tesseract OCR and image preprocessing for text recognition.
- Normalizes extracted fields for structured comparison.
- Supports inspection decisions and reporting of missing or inconsistent fields.

### 2. Windows Desktop Application
- Provides a desktop graphical interface for inspection workflows.
- Enables inspection of sample packaging images.
- Displays extracted information and verification results.
- Supports demonstration of OCR and track-and-trace functionality.

### 3. QR Code and Data Matrix Verification
- Includes processing workflows for QR Codes and Data Matrix symbols.
- Parses encoded payloads into structured fields.
- Compares encoded information against OCR-extracted printed information.
- Identifies missing or mismatched values for review.

Barcode decoding depends on the installed libraries and image quality. Real camera integration and industrial scanning performance require separate validation.

### 4. Pharmaceutical Serialization and Aggregation
- Demonstrates serialization-related verification using product and packaging identifiers.
- Includes track-and-trace data handling with SQLite-based storage.
- Supports aggregation concepts for relationships between packaging units.
- Provides sample workflows intended to illustrate traceability logic.

These are demonstration workflows, not certified implementations of pharmaceutical serialization standards.

### 5. Robustness Testing
- Includes a synthetic benchmark containing 250 image variations.
- Tests scenarios involving blur, rotation, lighting changes, damaged codes, and incorrect batch or expiry information.
- Provides evaluation scripts for inspecting OCR and verification performance.
- Supports reproducible experimentation using accompanying ground-truth CSV files.

### 6. Software Engineering and Automation
- FastAPI-based inspection endpoint.
- Automated tests using pytest.
- Docker configuration for the API.
- GitHub Actions continuous-integration workflow.
- Separation of application modules, evaluation scripts, tests, and sample data.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Computer vision | OpenCV, image preprocessing |
| OCR | Tesseract OCR |
| Backend | FastAPI |
| Desktop application | Python GUI |
| Data storage | SQLite |
| Testing | pytest |
| Containerization | Docker |
| CI | GitHub Actions |
| Data processing | JSON, CSV |
| Development | Git, GitHub, VS Code |

---

## Project Structure

```text
OCR_Dharati/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   ├── __init__.py
│   ├── advanced.py
│   ├── desktop.py
│   ├── field_normalization.py
│   ├── main.py
│   ├── payload_parser.py
│   ├── track_trace.py
│   └── verification.py
│
├── sample_data/
│   ├── carton.png
│   ├── benchmark_50/
│   └── robust_250/
│
├── scripts/
│   ├── evaluate_50.py
│   ├── evaluate_ocr_accuracy.py
│   ├── evaluate_robust.py
│   ├── evaluate_track_trace.py
│   ├── generate_robust_dataset.py
│   └── track_trace_demo.py
│
├── tests/
│
├── desktop_launcher.py
├── desktop_requirements.txt
├── RUN_DESKTOP_WINDOWS.bat
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── pytest.ini
└── README.md
```

---

## System Architecture

The application contains two complementary workflows.

**OCR Inspection API**

```text
Input Image
    |
    v
Image Validation
    |
    v
Image Preprocessing
    |
    v
Tesseract OCR
    |
    v
Text Extraction
    |
    v
Field Parsing and Normalization
    |
    v
Structured Inspection Result
    |
    v
JSON Response
```

**Desktop Verification and Track-and-Trace Workflow**

```text
Packaging Image
    |
    v
OCR and Barcode Processing
    |
    v
Printed / Encoded Field Extraction
    |
    v
Field Normalization
    |
    v
Verification and Mismatch Detection
    |
    v
Inspection Decision
    |
    v
Track-and-Trace Demonstration
```

The exact processing path depends on the selected workflow and available decoding components.

---

## Installation

### Prerequisites

- Python 3.11 or newer, with compatible project dependencies
- Tesseract OCR installed locally
- Windows for the intended desktop application workflow
- Git (optional)
- Docker (optional, for the API container)

### 1. Clone the Repository

```bash
git clone https://github.com/dharati-cv-ml/OCR_Dharati.git
cd OCR_Dharati
```

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Tesseract OCR

Install Tesseract OCR and ensure the `tesseract` executable is available on your system PATH.

Official project:

https://github.com/tesseract-ocr/tesseract

For Windows installations, a commonly used installation location is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Check the installation:

```powershell
tesseract --version
```

If Tesseract is installed but not found, add its installation directory to PATH or configure the executable path in the application.

---

## Running the Windows Desktop Application

Install the desktop requirements:

```powershell
python -m pip install -r desktop_requirements.txt
```

Launch the application:

```powershell
python -m app.desktop
```

Alternatively, use the provided Windows launcher:

```powershell
.\RUN_DESKTOP_WINDOWS.bat
```

The desktop application provides the primary graphical demonstration of the inspection and verification workflows.

---

## Running the FastAPI Application

Install the development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open the API documentation:

http://localhost:8000/docs

The inspection endpoint accepts an uploaded packaging image:

```bash
curl -F "file=@sample_data/carton.png;type=image/png" http://localhost:8000/inspect
```

The response provides structured inspection information derived from the submitted image.

---

## Evaluation and Benchmarking

The repository includes synthetic datasets and evaluation scripts to support repeatable experiments.

### OCR Accuracy Demonstration

A previous in-sample synthetic benchmark reported:

**149 out of 150 OCR fields matched the ground truth after schema-aware corrections (99.33%).**

This result describes the specific synthetic evaluation and should not be interpreted as accuracy on unseen manufacturing images.

It does not establish production reliability or generalization to different cameras, printers, labels, or environmental conditions.

An evaluation artifact is included:

`ocr_accuracy_report.json`

### 50-Image Inspection Benchmark

The `sample_data/benchmark_50/` directory includes generated packaging samples and accompanying ground-truth data.

Run the corresponding evaluation:

```powershell
python -m scripts.evaluate_track_trace
```

This benchmark supports inspection and verification testing on a controlled synthetic sample set.

### 250-Image Robustness Benchmark

The `sample_data/robust_250/` directory contains 250 synthetic image variations with a ground-truth CSV.

| Test category | Intended challenge |
|---|---|
| Blur | Reduced character and code sharpness |
| Rotation | Changes in image orientation |
| Lighting | Changes in illumination and contrast |
| Damaged code | Degraded barcode readability |
| Wrong batch / expiry | Deliberate inconsistencies in packaging information |

Run the robustness evaluation:

```powershell
python -m scripts.evaluate_robust
```

The evaluation is designed to measure performance under these simulated conditions. Reported results should be taken from actual evaluation output rather than assumed from the dataset size.

**Important:** No production accuracy, industrial throughput, false-accept rate, or real-camera reliability is claimed without corresponding measured evidence.

---

## Automated Testing

Run the available tests:

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

The test suite covers application behavior and sample inspection, verification, and track-and-trace workflows.

The repository also includes a GitHub Actions workflow:

`.github/workflows/ci.yml`

CI execution results can be viewed in the GitHub Actions tab.

---

## Docker

Build the API image:

```bash
docker build -t visioninspect-pro .
```

Run the container:

```bash
docker run --rm -p 8000:8000 visioninspect-pro
```

Open:

http://localhost:8000/docs

Docker support is intended for the API demonstration, not the Windows desktop interface.

---

## Engineering Considerations

This project demonstrates the integration of computer vision components with backend services, structured validation, local persistence, and automated testing.

Important engineering considerations include:

- **Image variability:** OCR performance is sensitive to blur, resolution, lighting, orientation, and print quality.
- **Field extraction:** Rule-based parsing and normalization depend on supported label formats.
- **Barcode reliability:** QR and Data Matrix decoding must be evaluated independently from OCR recognition.
- **Verification:** Printed and encoded values can be inconsistent even when individual recognition components work correctly.
- **Traceability:** Serialization and aggregation require consistent identifiers, data integrity, and appropriate transaction handling.
- **Performance:** Industrial latency and throughput require testing on representative hardware and real camera inputs.

---

## Limitations

- Synthetic data does not fully represent factory-floor image variability.
- Real camera capture and production-line integration have not been validated.
- Industrial throughput and end-to-end latency require controlled measurement.
- The system is not validated for GMP, GxP, or regulated pharmaceutical deployment.
- Serialization and aggregation are engineering demonstrations rather than production traceability services.
- Additional validation is required for unreadable codes, ambiguous text, unsupported formats, and other edge cases.

---

## Future Improvements

- Extend testing to independently collected, licensed packaging images.
- Improve OCR region detection and image enhancement for difficult printing conditions.
- Benchmark QR and Data Matrix decoding under broader image degradation scenarios.
- Add richer inspection analytics and visual reporting.
- Introduce additional unit, integration, and end-to-end tests.
- Measure latency distributions and resource utilization on target hardware.
- Improve configuration, logging, error handling, and deployment documentation.

---

## Legal and Attribution

All included sample packaging data is synthetic.

This repository is an independent portfolio demonstration and does not include confidential employer source code, proprietary production datasets, or customer information.

The repository's own source code is distributed under the included MIT License. Third-party dependencies, including Tesseract OCR, remain subject to their respective licenses.

---

## Author

**Dharati Trivedi**

AI Engineer | Machine Learning | Computer Vision | Industrial OCR & Inspection Systems

GitHub: https://github.com/dharati-cv-ml

---

**Disclaimer:** VisionInspect Pro is an engineering and research demonstration, not a certified pharmaceutical manufacturing, inspection, or regulatory compliance system.
