
import cv2
import pytesseract
import numpy as np

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    thresh = cv2.adaptiveThreshold(denoised, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    return thresh

def extract_text(image_path):
    preprocessed = preprocess_image(image_path)
    text = pytesseract.image_to_string(preprocessed, config='--psm 6')
    return text.strip()
