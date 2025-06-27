import tkinter as tk
from tkinter import filedialog, Label, Button, Text
from PIL import ImageTk, Image
import pytesseract
import re
import cv2
from pprint import pprint

# Explicitly set path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
    blur = cv2.GaussianBlur(contrast, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite("debug_output.png", thresh)
    return thresh

def extract_text_from_image(image_path):
    processed_img = preprocess_image(image_path)
    text_versions = {}

    for psm in [11, 6, 7]:
        config = f'--oem 3 --psm {psm}'
        try:
            text = pytesseract.image_to_string(processed_img, config=config).strip()
            text_versions[f'psm_{psm}'] = text
            print(f"[DEBUG] OCR with --psm {psm}: {text}")
        except Exception as e:
            print(f"[ERROR] OCR failed with --psm {psm}: {e}")

    # Save all attempts to file
    with open("last_ocr_output_all_modes.txt", "w", encoding="utf-8") as f:
        for mode, result in text_versions.items():
            f.write(f"=== {mode} ===\n{result}\n\n")

    # Use the one that contains expected keywords
    for text in text_versions.values():
        if "EXP" in text or "BATCH" in text:
            return text.upper()

    return next(iter(text_versions.values())).upper() if text_versions else ""

def verify_ocv_patterns(text):
    checks = {
        "BATCH": r"BATCH[:\s]*([A-Z0-9]+)",
        "EXPIRY_DATE": r"EXP[:\s]*([0-1][0-9]/\d{2})"
    }
    results = {}
    for label, pattern in checks.items():
        match = re.search(pattern, text)
        results[label] = "PASS" if match else "FAIL"
    return results

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pharmaceutical OCR + OCV Verifier")
        self.root.geometry("800x600")

        self.label = Label(root, text="Select a pharmaceutical label image", font=("Arial", 14))
        self.label.pack(pady=10)

        self.image_label = Label(root)
        self.image_label.pack()

        self.result_text = Text(root, height=10, width=80)
        self.result_text.pack(pady=10)

        self.select_button = Button(root, text="Select Image", command=self.load_image)
        self.select_button.pack(pady=5)

        self.verify_button = Button(root, text="Run OCR + OCV", command=self.run_ocr_ocv)
        self.verify_button.pack(pady=5)

        self.current_image_path = None

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.current_image_path = file_path
            img = Image.open(file_path)
            img.thumbnail((400, 300))
            self.tk_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.tk_image)
            self.result_text.delete(1.0, tk.END)

    def run_ocr_ocv(self):
        if not self.current_image_path:
            return

        text = extract_text_from_image(self.current_image_path)
        result = verify_ocv_patterns(text)

        output = f"Extracted Text:\n{text}\n\nOCV Results:\n"
        for key, val in result.items():
            output += f"{key}: {val}\n"

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, output)

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()