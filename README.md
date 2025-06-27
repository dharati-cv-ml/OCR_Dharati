# Pharmaceutical OCR + OCV GUI

This is a Tkinter-based GUI project to extract and verify `EXP` and `BATCH` information from pharmaceutical product labels using Tesseract OCR.

## Features

- Multi-mode OCR (`psm 6`, `7`, `11`)
- OpenCV preprocessing (contrast + threshold)
- Regex-based OCV verification
- Debugging: saves preprocessed image and all OCR outputs

## How to Run

```bash
python pharma_gui.py
