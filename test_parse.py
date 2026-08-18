import pymupdf, sys
from src.zscore_extractor.parsing import extract_headers
pdf = pymupdf.open('data/raw/COP_2023_2024.pdf')
headers = extract_headers(pdf[3]) # Page 4 (0-indexed 3)
for i, h in enumerate(headers):
    print(f"{i+1}: Course: {h['CourseName']} | Uni: {h['UniversityName']}")
