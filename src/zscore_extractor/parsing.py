from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Tuple

import pymupdf
import pandas as pd
import pdfplumber

from .config import DISTRICTS


def clean_text(value: str | None) -> str:
    """Collapse PDF whitespace while preserving the actual wording."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def make_id(prefix: str, text: str) -> str:
    """Stable ID from the entity name, preferring official UGC codes if available."""
    from .ugc_codes import get_course_code, get_university_code
    
    if prefix == "COURSE":
        code = get_course_code(text)
        if code:
            return code
    elif prefix == "UNIVERSITY":
        code = get_university_code(text)
        if code:
            return code
            
    digest = hashlib.sha1(text.upper().encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}_{digest}"


def parse_course_flags(course_name: str) -> tuple[str, bool]:
    """Remove markers for aptitude tests."""
    aptitude_test = "#" in course_name

    cleaned = course_name.replace("*", "").replace("#", "")
    # Deal with leftover trailing hyphens
    cleaned = cleaned.rstrip(" -")
    return clean_text(cleaned), aptitude_test


def normalize_university_name(name: str) -> str:
    """Standardize known university/institute name variants."""
    text = clean_text(name)
    text = text.replace(" -Trincomalee", " - Trincomalee")
    text = text.rstrip(",")

    alias_map = {
        "University of Jayewardenepura": "University of Sri Jayewardenepura",
        "University of Sabaragamuwa": "Sabaragamuwa University of Sri Lanka",
        "The Gampaha Wickramarachchi University of Indigenous": "The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka",
        "Gampaha Wickramarachchi University of Indigenous Medicine": "The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka",
        "Gampaha Wickramarachchi University of Indigenous Medicine,": "The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka",
        "Gampaha Wickramaarachchi Ayurveda Institute": "The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka",
        "Institute of Indigenous Medicine": "The Gampaha Wickramarachchi University of Indigenous Medicine, Sri Lanka",
        "Trincomalee Campus, Eastern University, Sri Lanka": "Eastern University - Trincomalee Campus",
        "Eastern University -Trincomalee Campus": "Eastern University - Trincomalee Campus",
        "University of Jaffna - Vavuniya Campus": "University of Vavuniya, Sri Lanka",
    }

    return alias_map.get(text, text)


def is_valid_university_name(name: str) -> bool:
    """Filter obvious OCR/parser artifacts that are not institution names."""
    text = clean_text(name)
    if not text:
        return False
    if len(text) < 6:
        return False
    if text in {"TMLE", "ICT"}:
        return False
    if "HONOURS" in text:
        return False
    has_institution_keyword = any(
        kw in text for kw in ["University", "Institute", "Academy", "Campus"]
    )
    return has_institution_keyword


def normalize_course_name(name: str) -> str:
    """Standardize spacing and punctuation for course names."""
    text = clean_text(name)
    # Normalize ampersand to "AND" — UGC PDFs inconsistently use both forms
    # for the same course across different years, which fragments CourseIDs.
    text = re.sub(r"\s*&\s*", " AND ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,")
    return text


def extract_headers(page: pymupdf.Page) -> list[dict]:
    """Extract course/university header blocks from a PDF page."""
    items: list[tuple[float, tuple[float, float], str]] = []
    text = page.get_text("dict")

    for block in text["blocks"]:
        if block["type"] != 0:
            continue

        lines = block.get("lines", [])
        if not lines:
            continue

        block_text = " ".join(
            span["text"]
            for line in lines
            for span in line.get("spans", [])
        )
        block_text = clean_text(block_text)
        if not block_text:
            continue

        direction = lines[0].get("dir", (1, 0))
        items.append((block["bbox"][0], direction, block_text))

    items.sort(key=lambda x: x[0])

    headers: list[dict] = []
    pending_course_parts: list[str] = []
    pending_uni_parts: list[str] = []
    in_uni = False

    for _, direction, text_value in items:
        if direction[1] < -0.9 and abs(direction[0]) < 1e-6:
            cleaned_val = clean_text(text_value)
            if cleaned_val.startswith("("):
                lower_val = cleaned_val.lower()
                if any(kw in lower_val for kw in ["university", "institute", "campus", "academy"]):
                    in_uni = True
                
            if in_uni:
                pending_uni_parts.append(text_value)
                if cleaned_val.endswith(")"):
                    raw_course = clean_text(" ".join(pending_course_parts))
                    raw_uni = clean_text(" ".join(pending_uni_parts)).strip("() ")
                    course_name, aptitude_test = parse_course_flags(raw_course)
                    headers.append(
                        {
                            "CourseName": course_name,
                            "UniversityName": raw_uni,
                            "AptitudeTest": aptitude_test,
                        }
                    )
                    pending_course_parts = []
                    pending_uni_parts = []
                    in_uni = False
            else:
                pending_course_parts.append(text_value)

    if headers:
        return headers

    fallback_headers: list[dict] = []
    for x0, _, text_value in items:
        if x0 > 320:
            continue

        cleaned = clean_text(text_value)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered.startswith(("university admission", "minimum", "based on", "[based on", "course of study")):
            continue
        if "advanced level" in lowered or "examination" in lowered or "results of the g.c.e" in lowered:
            continue
        if "district" in lowered:
            continue
        if " (" not in cleaned:
            continue

        pieces = cleaned.rsplit(" (", 1)
        if len(pieces) != 2:
            continue
        course_part, university_part = pieces
        university = clean_text(university_part).rstrip(")")
        course_name = clean_text(course_part)
        if not course_name or not university:
            continue

        c_name, aptitude_test = parse_course_flags(course_name)
        fallback_headers.append(
            {
                "CourseName": c_name,
                "UniversityName": university,
                "AptitudeTest": aptitude_test,
            }
        )

    return fallback_headers


def extract_page_table(pdf_page, page_number: int) -> list[list[str]]:
    """Extract the main cutoff table from one PDF page."""
    tables = pdf_page.extract_tables()
    if not tables:
        raise ValueError(f"Page {page_number}: no table detected.")

    table = tables[0]
    cleaned_rows = []
    for row in table:
        if not row:
            continue
        cleaned_rows.append([clean_text(cell) for cell in row])

    while cleaned_rows and all(not row[-1] for row in cleaned_rows):
        for row in cleaned_rows:
            row.pop()

    return cleaned_rows


def parse_cutoff(value: str):
    """Return (numeric_value, status) while preserving NQC as a status."""
    value = clean_text(value).upper()

    if not value:
        return None, "MISSING"
    if value == "NQC":
        return None, "NQC"

    try:
        return float(value), "AVAILABLE"
    except ValueError:
        return None, f"UNPARSED:{value}"


def infer_year_metadata(pdf_path: Path) -> tuple[str, int, str, str]:
    """Infer academic-year metadata from filenames like COP_2018_2019.pdf."""
    match = re.search(r"(\d{4})_(\d{4})", pdf_path.stem)
    if not match:
        raise ValueError(
            f"Could not infer academic year from file name: {pdf_path.name}"
        )

    start_year = int(match.group(1))
    end_year = int(match.group(2))
    academic_year = f"{start_year}/{end_year}"
    year_id = f"YEAR_{start_year}_{end_year}"

    # Publication date is standardized as end-of-July of the second year.
    publication_date = f"{end_year}-07-31"
    exam_year = start_year

    return academic_year, exam_year, publication_date, year_id


def extract_pdf(pdf_path: Path, output_dir: Path, write_csv: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Extract a PDF and optionally write CSV outputs into `output_dir`."""
    if write_csv:
        output_dir.mkdir(parents=True, exist_ok=True)

    academic_year, exam_year, publication_date, year_id = infer_year_metadata(pdf_path)

    pdf = pymupdf.open(pdf_path)
    fact_rows: List[dict] = []
    validation: List[str] = []

    with pdfplumber.open(pdf_path) as plumber_pdf:
        if len(pdf) != len(plumber_pdf.pages):
            raise ValueError("PyMuPDF and pdfplumber page counts do not match.")

        for page_index, plumber_page in enumerate(plumber_pdf.pages):
            page_number = page_index + 1
            pymupdf_page = pdf[page_index]

            headers = extract_headers(pymupdf_page)
            table = extract_page_table(plumber_page, page_number)

            if not table:
                raise ValueError(f"Page {page_number}: empty table.")

            # --- Reorder headers to match pdfplumber column order ---
            # The pdfplumber header row contains reversed text for rotated
            # columns (e.g. ")obmoloC fo ENICIDEM ytisrevinU(" which is
            # "MEDICINE (University of Colombo)" reversed).  We use this to
            # determine the true left-to-right column order and re-sort the
            # headers that extract_headers() returned in an arbitrary order.
            header_row_cells = table[0][1:]  # skip the "DISTRICT" cell
            if len(header_row_cells) == len(headers) and len(headers) > 1:
                reordered: list[dict] = []
                used: list[bool] = [False] * len(headers)

                for cell_text in header_row_cells:
                    if not cell_text:
                        # If the header cell is empty, fall back to order
                        for idx, h in enumerate(headers):
                            if not used[idx]:
                                reordered.append(h)
                                used[idx] = True
                                break
                        continue

                    # Reverse the cell text to get the readable form
                    reversed_cell = cell_text[::-1].upper()
                    # Clean up whitespace
                    reversed_cell = re.sub(r"\s+", " ", reversed_cell).strip()

                    # Find the best matching header by checking if both the
                    # course name and a university keyword appear in the cell
                    best_idx = -1
                    best_score = -1
                    for idx, h in enumerate(headers):
                        if used[idx]:
                            continue
                        course_upper = h["CourseName"].upper()
                        uni_upper = h["UniversityName"].upper()

                        # Split course into words and count matches
                        course_words = course_upper.split()
                        uni_words = uni_upper.split()
                        score = 0
                        for w in course_words:
                            if len(w) >= 3 and w in reversed_cell:
                                score += 1
                        for w in uni_words:
                            if len(w) >= 3 and w in reversed_cell:
                                score += 1

                        if score > best_score:
                            best_score = score
                            best_idx = idx

                    if best_idx >= 0:
                        reordered.append(headers[best_idx])
                        used[best_idx] = True
                    else:
                        # Shouldn't happen, but fall back to next unused
                        for idx, h in enumerate(headers):
                            if not used[idx]:
                                reordered.append(h)
                                used[idx] = True
                                break

                headers = reordered

            data_rows = [
                row for row in table[1:]
                if row and clean_text(row[0]) in DISTRICTS
            ]
            found_districts = [clean_text(row[0]).upper() for row in data_rows]

            if len(found_districts) != len(DISTRICTS):
                raise ValueError(
                    f"Page {page_number}: expected {len(DISTRICTS)} districts, "
                    f"found {len(found_districts)}. Found: {found_districts}"
                )

            if found_districts != DISTRICTS:
                raise ValueError(
                    f"Page {page_number}: district order changed.\n"
                    f"Expected: {DISTRICTS}\n"
                    f"Found:    {found_districts}"
                )

            value_column_count = len(data_rows[0]) - 1
            if value_column_count != len(headers):
                raise ValueError(
                    f"Page {page_number}: header/table mismatch. "
                    f"Extracted {len(headers)} course-university headers but "
                    f"{value_column_count} cutoff columns."
                )

            validation.append(
                f"Page {page_number}: "
                f"{len(headers)} courses × {len(data_rows)} districts = "
                f"{len(headers) * len(data_rows)} cells"
            )

            for row in data_rows:
                district_name = clean_text(row[0]).upper()
                district_id = make_id("DISTRICT", district_name)

                for col_index, header in enumerate(headers, start=1):
                    cutoff_z, cutoff_status = parse_cutoff(row[col_index])
                    course_name = normalize_course_name(header["CourseName"])
                    university_name = normalize_university_name(header["UniversityName"])

                    if not is_valid_university_name(university_name):
                        continue

                    fact_rows.append(
                        {
                            "YearID": year_id,
                            "CourseID": make_id("COURSE", course_name),
                            "UniversityID": make_id("UNIVERSITY", university_name),
                            "DistrictID": district_id,
                            "CutoffZ": cutoff_z,
                            "CutoffStatus": cutoff_status,
                            "AptitudeTest": header["AptitudeTest"],
                            "Page": page_number,
                            "SourceFile": pdf_path.name,
                            # Keep these temporarily to build dims later in the function, but drop them from final fact
                            "_CourseName": course_name,
                            "_UniversityName": university_name,
                            "_DistrictName": district_name,
                            "_AcademicYear": academic_year,
                            "_ExamYear": exam_year,
                            "_PublicationDate": publication_date,
                        }
                    )

    fact = pd.DataFrame(fact_rows)

    course_dim = (
        fact[["CourseID", "_CourseName"]]
        .rename(columns={"_CourseName": "CourseName"})
        .drop_duplicates()
        .sort_values("CourseName")
        .reset_index(drop=True)
    )
    university_dim = (
        fact[["UniversityID", "_UniversityName"]]
        .rename(columns={"_UniversityName": "UniversityName"})
        .drop_duplicates()
        .sort_values("UniversityName")
        .reset_index(drop=True)
    )
    district_dim = pd.DataFrame(
        {
            "DistrictID": [make_id("DISTRICT", d) for d in DISTRICTS],
            "DistrictName": DISTRICTS,
        }
    )
    year_dim = pd.DataFrame(
        [
            {
                "YearID": year_id,
                "AcademicYear": academic_year,
                "ExamYear": exam_year,
                "PublicationDate": publication_date,
            }
        ]
    )

    fact_columns = [
        "YearID",
        "CourseID",
        "UniversityID",
        "DistrictID",
        "CutoffZ", "CutoffStatus",
        "AptitudeTest",
        "Page", "SourceFile",
    ]
    # Sort using the temporary columns before dropping them
    fact = fact.sort_values(["_CourseName", "_UniversityName", "_DistrictName"])
    fact = fact[fact_columns].reset_index(drop=True)

    if write_csv:
        fact.to_csv(output_dir / "fact_cutoffs.csv", index=False, encoding="utf-8-sig")
        course_dim.to_csv(output_dir / "dim_course.csv", index=False, encoding="utf-8-sig")
        university_dim.to_csv(output_dir / "dim_university.csv", index=False, encoding="utf-8-sig")
        district_dim.to_csv(output_dir / "dim_district.csv", index=False, encoding="utf-8-sig")
        year_dim.to_csv(output_dir / "dim_year.csv", index=False, encoding="utf-8-sig")

    report_lines = [
        "Sri Lanka A/L UGC cutoff extraction validation",
        f"Source: {pdf_path.name}",
        f"Academic year: {academic_year}",
        f"Total fact rows: {len(fact):,}",
        f"Unique courses: {fact['CourseID'].nunique():,}",
        f"Unique universities: {fact['UniversityID'].nunique():,}",
        f"Districts: {fact['DistrictID'].nunique():,}",
        "",
        *validation,
        "",
        "Cutoff status counts:",
        fact["CutoffStatus"].value_counts(dropna=False).to_string(),
        "",
        "NQC cells:",
        str((fact["CutoffStatus"] == "NQC").sum()),
        "",
        "Unparsed values:",
        str(fact[fact["CutoffStatus"].str.startswith("UNPARSED:")].shape[0]),
    ]

    if write_csv:
        (output_dir / "validation_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("\nExtraction complete.")
    if write_csv:
        print(f"Output directory: {output_dir.resolve()}")
    print(f"Fact rows:        {len(fact):,}")
    print(f"Courses:          {fact['CourseID'].nunique():,}")
    print(f"Universities:     {fact['UniversityID'].nunique():,}")
    print(f"Districts:        {fact['DistrictID'].nunique():,}")
    print(f"NQC cells:        {(fact['CutoffStatus'] == 'NQC').sum():,}")

    return fact, course_dim, university_dim, district_dim, year_dim
