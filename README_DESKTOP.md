# VisionInspect — Desktop OCR Studio

A **real Windows desktop GUI** for the Industrial OCR Inspection API. Runs locally with **no website, no HTTP server, no cloud and no account**.

## Features
- Open individual photos or process a complete folder
- Display an image preview and full extracted text
- Extract product code (SKU/PRODUCT/GTIN), batch (LOT/BATCH), and expiry (EXP/EXPIRY)
- Flag missing fields, display pass/review, and track scan totals
- Browse inspection history, copy text, export CSV and JSON
- Responsive background scanning (window stays usable)
- Keep original FastAPI project and tests unchanged

## Windows — first-time setup

1. Install **Python 3.11** from https://www.python.org/downloads/ (check *Add Python to PATH*).
2. Install the **Tesseract OCR engine** for Windows. The community-maintained installer is linked from https://github.com/UB-Mannheim/tesseract/wiki . Its typical installation path is `C:\Program Files\Tesseract-OCR\tesseract.exe`. This is **different** from the `pytesseract` Python package.
3. Extract the ZIP into a normal folder, e.g. `C:\Users\YourName\ocr-desktop`.
4. **Double-click `RUN_DESKTOP_WINDOWS.bat`**. The first run creates `.venv`, installs packages, and opens the desktop window. Subsequent runs also check the dependencies.

Or in VS Code PowerShell, from the extracted root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop_requirements.txt
.\.venv\Scripts\python.exe -m app.desktop
```

**Do not** run `app/desktop.py` directly. Launch `python -m app.desktop` from the project root so imports work.

## Use it

1. Click **Select image** and choose a PNG/JPEG/WEBP/BMP/TIFF.
2. Click **Inspect image**. A packaging image with a readable printed SKU/LOT/EXP is best.
3. To inspect multiple images, use **Scan folder**.
4. Review the green PASS or red NEEDS REVIEW flag. Red means a required field was not found, *not necessarily that the physical package failed QA*.
5. Click **Export CSV** or **Export JSON** for your report. No data leaves your computer.

Test with the included `sample_data/carton.png` image.

## Troubleshooting

- **TESSERACT NOT FOUND**: install Tesseract and restart; the app checks PATH and standard Windows installation folders. Run `tesseract --version` in a new terminal to confirm if PATH is set.
- **No module named PIL**: use the exact project environment, e.g. `.\.venv\Scripts\python.exe -m pip install -r desktop_requirements.txt`.
- **Python 3.14**: Python 3.11 is recommended to avoid future ML compatibility issues.
- **Cannot open the app**: launch from a terminal using `.\.venv\Scripts\python.exe -m app.desktop` and read the error.
- **OCR misses text**: use a high-resolution, non-blurry image with large legible text. OCR is not guaranteed. Field patterns are intentionally simple and can be customized in `app/main.py`.
- **Size limits**: 8 MB per image, 15 million pixels.

## Optional: Create your own Windows EXE

After verifying the app on your machine:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onefile --name VisionInspect desktop_launcher.py
```

**Note:** Tesseract OCR must still be installed separately; a basic PyInstaller bundle does not include its binary. Build the EXE on Windows after you verify the Python version works. The simplest supported launch is `RUN_DESKTOP_WINDOWS.bat`.

## Portfolio note

This is a local OCR prototype. Results should be evaluated with a labeled dataset before making reliability or industrial inspection accuracy claims. The application does not decode Data Matrix codes or verify physical print quality.
