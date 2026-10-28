import pdfplumber
import re
from pathlib import Path
import pandas as pd
from typing import Dict, Tuple
from difflib import get_close_matches

from zscore_extractor.parsing import normalize_course_name, normalize_university_name, clean_text

_course_code_map = {}
_uni_code_map = {}
_code_to_canonical_course = {}
_is_loaded = False

COURSE_OVERRIDES = {
    'DATA SCIENCE': '136',
    'ANIMAL SCIENCE': '067',
    'ANIMAL PRODUCTION AND FOOD TECHNOLOGY': '067',
    'ANIMAL SCIENCE AND FISHERIES': '086',
    'ANIMAL SCIENCE & FISHERIES': '086',
    'APPLIED SCIENCES (BIO.SC)': '007',
    'APPLIED SCIENCES (BIOLOGICAL SC.)': '007',
    'APPLIED SCIENCES (BIOLOGICAL SCIENCE)': '007',
    'APPLIED SCIENCES (PHY.SC)': '015',
    'APPLIED SCIENCES (PHYSICAL SC.)': '015',
    'APPLIED SCIENCES (PHYSICAL SCIENCE)': '015',
    'ARTS (SAB) - A [ARTS STREAM]': '021',
    'ARTS (SAB) - B [COMMERCE STREAM]': '021',
    'ARTS (SAB)': '021',
    'ARTS(SAB)': '021',
    'ARTS (SP) / MASS MEDIA': '020',
    'ARTS (SP) - MASS MEDIA': '020',
    'ARTS (SP) / PERFORMING ARTS': '041',
    'ARTS (SP) - PERFORMING ARTS': '041',
    'ESTATE MANAGEMENT AND VALUATION': '017',
    'REAL ESTATE MANAGEMENT AND VALUATION': '017',
    'MANAGEMENT (PUBLIC) (SPECIAL)': '028',
    'MANAGEMENT (PUBLIC) SPECIAL': '028',
    'MANAGEMENT (PUBLIC) HONOURS': '028',
    'MANAGEMENT AND PUBLIC POLICY': '028',
    'FOOD BUSINESS MANAGEMENT [BIOLOGICAL / PHYSICAL SCIENCE STREAM]': '107',
    'FOOD BUSINESS MANAGEMENT [COMMERCE STREAM]': '107',
    'FOOD BUSINESS MANAGEMENT': '107',
    'MANAGEMENT STUDIES (TV) - A [COMMERCE STREAM]': '022',
    'MANAGEMENT STUDIES (TV) - B [ANY SUBJECT COMBINATION]': '022',
    'MANAGEMENT STUDIES (TV)': '022',
    'TRANSPORT AND LOGISTICS MANAGEMENT': '057',
    'TRANSPORT MANAGEMENT AND LOGISTICS ENGINEERING (TMLE)': '057',
    'TRANSPORT MANAGEMENT & LOGISTICS ENGINEERING (TMLE)': '057',
    'MOLECULAR BIOLOGY AND BIOCHEMISTRY': '058',
    'BIOCHEMISTRY AND MOLECULAR BIOLOGY': '058',
    'BIOCHEMISTRY & MOLECULAR BIOLOGY': '058',
    'TOWN AND COUNTRY PLANNING': '030',
    'URBAN INFORMATICS AND PLANNING': '030',
    'TEA TECHNOLOGY AND VALUE ADDITION': '135',
    'TEA TECHNOLOGY & VALUE ADDITION': '135',
    'PALM AND LATEX TECHNOLOGY AND VALUE ADDITION': '135',
    'PALM AND LATEX TECHNOLOGY & VALUE ADDITION': '135',
    'PLANTATION MANAGEMENT AND TECHNOLOGY': '135',
    'SERVICE MANAGEMENT': '140',
    'INDIGENOUS MEDICINAL RESOURCES': '120',
    'HEALTH INFORMATION AND COMMUNICATION TECHNOLOGY': '121',
    'HEALTH TOURISM AND HOSPITALITY MANAGEMENT': '122',
    'BIOMEDICAL TECHNOLOGY': '123',
    'INDIGENOUS PHARMACEUTICAL TECHNOLOGY': '124',
    'YOGA AND PARAPSYCHOLOGY': '125',
    'SOCIAL STUDIES IN INDIGENOUS KNOWLEDGE': '126',
    'ACCOUNTING INFORMATION SYSTEMS': '127',
    'COMPUTING AND INFORMATION SYSTEMS': '080',
    'COMPUTING & INFORMATION SYSTEMS': '080',
    'BUSINESS INFORMATION SYSTEMS (SPECIAL)': '077',
    'BUSINESS INFORMATION SYSTEMS (SPECIAL) (BIS)': '077',
    'BUSINESS INFORMATION SYSTEMS (HONOURS) (BIS)': '077',
    'MANAGEMENT AND INFORMATION TECHNOLOGY (MIT) (BIO SCIENCE STREAM)': '027',
    'MANAGEMENT AND INFORMATION TECHNOLOGY (MIT) (OTHER STREAM)': '027',
    'MANAGEMENT AND INFORMATION TECHNOLOGY (MIT)': '027',
    'MANAGEMENT AND INFORMATION TECHNOLOGY': '027',
    'SPORTS SCIENCE': '141',
    'GEOGRAPHICAL INFORMATION SYSTEMS': '142',
    'ELECTRONIC AND INTELLIGENT SYSTEMS ENGINEERING': '143',
    'COMPUTATION AND MANAGEMENT': '074',
    'COMPUTATION & MANAGEMENT': '074',
}

CANONICAL_NAMES = {
    '067': 'ANIMAL PRODUCTION AND FOOD TECHNOLOGY',
    '086': 'ANIMAL SCIENCE AND FISHERIES',
    '136': 'DATA SCIENCE',
    '020': 'ARTS (SP) - MASS MEDIA',
    '041': 'ARTS (SP) - PERFORMING ARTS',
    '021': 'ARTS (SAB)',
    '022': 'MANAGEMENT STUDIES (TV)',
    '028': 'MANAGEMENT AND PUBLIC POLICY',
    '030': 'URBAN INFORMATICS AND PLANNING',
    '057': 'TRANSPORT MANAGEMENT AND LOGISTICS ENGINEERING (TMLE)',
    '058': 'BIOCHEMISTRY AND MOLECULAR BIOLOGY',
    '074': 'COMPUTATION AND MANAGEMENT',
    '077': 'BUSINESS INFORMATION SYSTEMS (SPECIAL)',
    '080': 'COMPUTING AND INFORMATION SYSTEMS',
    '107': 'FOOD BUSINESS MANAGEMENT',
    '120': 'INDIGENOUS MEDICINAL RESOURCES',
    '121': 'HEALTH INFORMATION AND COMMUNICATION TECHNOLOGY',
    '122': 'HEALTH TOURISM AND HOSPITALITY MANAGEMENT',
    '123': 'BIOMEDICAL TECHNOLOGY',
    '124': 'INDIGENOUS PHARMACEUTICAL TECHNOLOGY',
    '125': 'YOGA AND PARAPSYCHOLOGY',
    '126': 'SOCIAL STUDIES IN INDIGENOUS KNOWLEDGE',
    '127': 'ACCOUNTING INFORMATION SYSTEMS',
    '135': 'PLANTATION MANAGEMENT AND TECHNOLOGY',
    '138': 'MEDICAL IMAGING TECHNOLOGY',
    '140': 'SERVICE MANAGEMENT',
    '141': 'SPORTS SCIENCE',
    '142': 'GEOGRAPHICAL INFORMATION SYSTEMS',
    '143': 'ELECTRONIC AND INTELLIGENT SYSTEMS ENGINEERING',
}


def _fuzzy_match(target: str, choices: list[str], threshold: float = 0.85) -> str | None:
    # Exact match first
    if target in choices:
        return target
    
    # Try removing punctuation and extra spaces
    t_clean = re.sub(r'[^A-Z0-9]', '', target)
    for c in choices:
        if t_clean == re.sub(r'[^A-Z0-9]', '', c):
            return c
            
    matches = get_close_matches(target, choices, n=1, cutoff=threshold)
    if matches:
        return matches[0]
    return None


def load_ugc_codes():
    global _course_code_map, _uni_code_map, _code_to_canonical_course, _is_loaded
    if _is_loaded:
        return
    
    course_to_code = {}
    uni_to_code = {}
    code_to_name = dict(CANONICAL_NAMES)
    
    raw_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'raw'
    
    # 1. Ingest official course codes and names from all SEATS PDFs
    for pdf_path in sorted(raw_dir.glob('SEATS_*.pdf')):
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                for row in tables[0]:
                    if len(row) < 2 or not row[0] or not row[0].strip().isdigit():
                        continue
                    code = row[0].strip().zfill(3)
                    name_raw = clean_text(row[1])
                    name_clean = re.sub(r'\(New\)|\(NEW\)', '', name_raw, flags=re.IGNORECASE).strip()
                    c_norm = normalize_course_name(name_clean).upper()
                    course_to_code[c_norm] = code
                    if code not in code_to_name:
                        code_to_name[code] = c_norm

    # 2. Ingest course and university codes from UNICODES.pdf
    pdf_path = raw_dir / 'UNICODES.pdf'
    if pdf_path.exists():
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                for row in tables[0]:
                    if len(row) < 4 or row[1] == 'COURSE OF STUDY' or row[1] is None:
                        continue
                    
                    course_raw = clean_text(row[1])
                    uni_raw = clean_text(row[2])
                    unicode_str = clean_text(row[3])
                    
                    if not unicode_str:
                        continue
                    match = re.match(r'^(\d+)([A-Z]+)$', unicode_str)
                    if match:
                        c_code, u_code = match.groups()
                        c_code = c_code.zfill(3)
                        c_norm = normalize_course_name(course_raw).upper()
                        u_norm = normalize_university_name(uni_raw).upper()
                        
                        if c_norm not in course_to_code:
                            course_to_code[c_norm] = c_code
                        uni_to_code[u_norm] = u_code
                        if c_code not in code_to_name:
                            code_to_name[c_code] = c_norm

    # 3. Apply canonical course overrides
    for k, v in COURSE_OVERRIDES.items():
        course_to_code[k] = v

    _course_code_map = course_to_code
    _uni_code_map = uni_to_code
    _code_to_canonical_course = code_to_name
    _is_loaded = True


def get_course_code(course_name: str) -> str | None:
    load_ugc_codes()
    norm = normalize_course_name(course_name).upper()
    
    # Check overrides directly
    if norm in COURSE_OVERRIDES:
        return COURSE_OVERRIDES[norm]
        
    # Check direct dictionary match
    if norm in _course_code_map:
        return _course_code_map[norm]
        
    # Strict fuzzy match with 0.85 threshold to avoid false cross-course collisions
    match = _fuzzy_match(norm, list(_course_code_map.keys()), threshold=0.85)
    if match:
        return _course_code_map[match]
    return None


def get_canonical_course_name(course_id: str, default_name: str = "") -> str:
    load_ugc_codes()
    cid = str(course_id).strip().zfill(3)
    return _code_to_canonical_course.get(cid, default_name)


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
    
    raw_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'raw'
    for pdf_path in raw_dir.glob('SEATS_*.pdf'):
        match = re.search(r'SEATS_(\d{4}_\d{4})\.pdf', pdf_path.name)
        if not match:
            continue
        academic_year = match.group(1).replace('_', '/')
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for row in tables[0]:
                    if len(row) < 4:
                        continue
                    code = clean_text(row[0])
                    if not code or not code.isdigit():
                        continue
                    
                    intake = clean_text(row[3])
                    if intake and intake.isdigit():
                        records.append({
                            'AcademicYear': academic_year,
                            'CourseID': code.zfill(3),
                            'Intake': int(intake)
                        })
                        
    return pd.DataFrame(records)


if __name__ == '__main__':
    load_ugc_codes()
    print(f"Loaded {len(_course_code_map)} courses, {len(_uni_code_map)} unis")
    print(f"Code for DATA SCIENCE: {get_course_code('DATA SCIENCE')}")
    print(f"Code for ANIMAL SCIENCE: {get_course_code('ANIMAL SCIENCE')}")
    print(f"Canonical name for 136: {get_canonical_course_name('136')}")
    print(f"Canonical name for 067: {get_canonical_course_name('067')}")
