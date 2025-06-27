
import json
import re

def load_expected_values(filepath='expected_data/expected_values.json'):
    with open(filepath, 'r') as f:
        return json.load(f)

def verify_text(extracted_text, expected_values):
    results = {}
    for key, expected in expected_values.items():
        if re.search(expected, extracted_text):
            results[key] = "PASS"
        else:
            results[key] = "FAIL"
    return results
