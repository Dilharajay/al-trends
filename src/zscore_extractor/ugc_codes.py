import pdfplumber
import re
from pathlib import Path
import pandas as pd
from typing import Dict, Tuple
from difflib import get_close_matches

from zscore_extractor.parsing import normalize_course_name, normalize_university_name, clean_text

_course_code_map = {}
_uni_code_map = {}
_is_loaded = False

def _fuzzy_match(target: str, choices: list[str], threshold: float = 0.8) -> str | None:
    # Exact match first
    if target in choices: return target
    
    # Try removing punctuation
    t_clean = re.sub(r'[^a-zA-Z0-9]', '', target)
    for c in choices:
        if t_clean == re.sub(r'[^a-zA-Z0-9]', '', c):
            return c
            
    matches = get_close_matches(target, choices, n=1, cutoff=threshold)
    if matches:
        return matches[0]
    return None

def load_ugc_codes():
    global _course_code_map, _uni_code_map, _is_loaded
    if _is_loaded: return
    
    course_to_code = {}
    uni_to_code = {}
    
    pdf_path = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'UNICODES.pdf'
    if not pdf_path.exists():
        return
        
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables: continue
            for row in tables[0]:
                if len(row) < 4: continue
                if row[1] == 'COURSE OF STUDY' or row[1] is None: continue
                
                course_raw = clean_text(row[1])
                uni_raw = clean_text(row[2])
                unicode_str = clean_text(row[3])
                
                if not unicode_str: continue
                match = re.match(r'^(\d+)([A-Z]+)$', unicode_str)
                if match:
                    c_code, u_code = match.groups()
                    c_norm = normalize_course_name(course_raw).upper()
                    u_norm = normalize_university_name(uni_raw).upper()
                    
                    course_to_code[c_norm] = c_code
                    uni_to_code[u_norm] = u_code
                    
    _course_code_map = course_to_code
    _uni_code_map = uni_to_code
    _is_loaded = True

def get_course_code(course_name: str) -> str | None:
    load_ugc_codes()
    norm = normalize_course_name(course_name).upper()
    
    # Custom overrides for tricky ones
    overrides = {
        'APPLIED SCIENCES (BIO.SC)': 'APPLIED SCIENCES (BIOLOGICAL SC.)',
        'APPLIED SCIENCES (PHY.SC)': 'APPLIED SCIENCES (PHYSICAL SC.)',
        'ARTS (SAB) - A [ARTS STREAM]': 'ARTS (SAB)',
        'ARTS (SAB) - B [COMMERCE STREAM]': 'ARTS (SAB)',
        'ARTS (SP) / MASS MEDIA': 'ARTS (SP)',
        'ARTS (SP) / PERFORMING ARTS': 'ARTS (SP)',
    }
    
    target = overrides.get(norm, norm)
    match = _fuzzy_match(target, list(_course_code_map.keys()), threshold=0.75)
    if match:
        return _course_code_map[match]
    return None

def get_university_code(university_name: str) -> str | None:
    load_ugc_codes()
    norm = normalize_university_name(university_name).upper()
    
    overrides = {
        'EASTERN UNIVERSITY - TRINCOMALEE CAMPUS': 'TRINCOMALEE CAMPUS, EASTERN UNIVERSITY, SRI LANKA',
        'UNIVERSITY OF COLOMBO - SRI PALEE CAMPUS': 'SRI PALEE CAMPUS, UNIVERSITY OF COLOMBO',
        'RAMANATHAN ACADEMY OF FINE ARTS': 'RAMANATHAN ACADEMY OF FINE ARTS, UNIVERSITY OF JAFFNA',
        'SWAMI VIPULANANDA INSTITUTE OF AESTHETIC STUDIES': 'SWAMI VIPULANANDA INSTITUTE OF AESTHETIC STUDIES, EASTERN UNIVERSITY, SRI LANKA'
    }
    
    target = overrides.get(norm, norm)
    match = _fuzzy_match(target, list(_uni_code_map.keys()), threshold=0.75)
    if match:
        return _uni_code_map[match]
    return None

def extract_all_intakes() -> pd.DataFrame:
    records = []
    import re
    
    raw_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    for pdf_path in raw_dir.glob('SEATS_*.pdf'):
        match = re.search(r'SEATS_(\d{4}_\d{4})\.pdf', pdf_path.name)
        if not match: continue
        academic_year = match.group(1).replace('_', '/')
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables: continue
                
                for row in tables[0]:
                    if len(row) < 4: continue
                    code = clean_text(row[0])
                    if not code or not code.isdigit(): continue
                    
                    intake = clean_text(row[3])
                    if intake and intake.isdigit():
                        records.append({
                            'AcademicYear': academic_year,
                            'CourseID': code,
                            'Intake': int(intake)
                        })
                        
    return pd.DataFrame(records)

if __name__ == '__main__':
    # Test everything
    load_ugc_codes()
    print(f"Loaded {len(_course_code_map)} courses, {len(_uni_code_map)} unis")
    
    import sqlite3
    conn = sqlite3.connect('data/bronze/db/al_cutoffs.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT CourseName FROM dim_course")
    db_courses = [row[0] for row in c.fetchall()]
    
    missing_c = []
    for c_name in db_courses:
        if not get_course_code(c_name):
            missing_c.append(c_name)
            
    print(f"Missing Courses after fuzzy ({len(missing_c)}): {missing_c[:5]}")
    
    c.execute("SELECT DISTINCT UniversityName FROM dim_university")
    db_unis = [row[0] for row in c.fetchall()]
    
    missing_u = []
    for u_name in db_unis:
        if not get_university_code(u_name):
            missing_u.append(u_name)
            
    print(f"Missing Unis after fuzzy ({len(missing_u)}): {missing_u}")
    
    df = extract_all_intakes()
    print(f"Extracted {len(df)} intake records. Sample:")
    print(df.head())
