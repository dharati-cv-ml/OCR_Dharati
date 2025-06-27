import os
from ocr_utils import extract_text
from ocv_checker import load_expected_values, verify_text
import pytesseract

# Explicitly set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def run_pipeline(image_path):
    print(f"\n[INFO] Processing: {image_path}")
    extracted_text = extract_text(image_path)
    print("[OCR] Extracted Text:\n", extracted_text)

    expected_values = load_expected_values()
    ocv_result = verify_text(extracted_text, expected_values)

    print("\n[OCV] Verification Results:")
    for key, result in ocv_result.items():
        print(f"{key}: {result}")

if __name__ == "__main__":
    images_dir = "data/sample_images"
    for filename in os.listdir(images_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            run_pipeline(os.path.join(images_dir, filename))
