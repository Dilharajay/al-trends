from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Tuple

import fitz
import pandas as pd
import pdfplumber

from .config import ACADEMIC_YEAR, DISTRICTS, EXAM_YEAR, PUBLICATION_DATE


def clean_text(value: str | None) -> str:
    """Collapse PDF whitespace while preserving the actual wording."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def make_id(prefix: str, text: str) -> str:
    """Stable ID from the entity name."""
    digest = hashlib.sha1(text.upper().encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}_{digest}"


def parse_course_flags(course_name: str) -> tuple[str, bool, bool]:
    """Remove markers for all-island merit and aptitude tests."""
    all_island_merit = "*" in course_name
    aptitude_test = "#" in course_name

    cleaned = course_name.replace("*", "").replace("#", "")
    cleaned = clean_text(cleaned)
    return cleaned, all_island_merit, aptitude_test


def extract_headers(page: fitz.Page) -> list[dict]:
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

    for _, direction, text_value in items:
        if direction[1] < -0.9 and abs(direction[0]) < 1e-6:
            if text_value.startswith("("):
                if pending_course_parts:
                    raw_course = clean_text(" ".join(pending_course_parts))
                    university = clean_text(text_value).strip("() ")
                    course_name, all_island_merit, aptitude_test = parse_course_flags(raw_course)
                    headers.append(
                        {
                            "CourseName": course_name,
                            "UniversityName": university,
                            "AllIslandMerit": all_island_merit,
                            "AptitudeTest": aptitude_test,
                        }
                    )
                    pending_course_parts = []
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

        c_name, all_island_merit, aptitude_test = parse_course_flags(course_name)
        fallback_headers.append(
            {
                "CourseName": c_name,
                "UniversityName": university,
                "AllIslandMerit": all_island_merit,
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


def extract_pdf(pdf_path: Path, output_dir: Path, write_csv: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Extract a PDF and optionally write CSV outputs into `output_dir`."""
    if write_csv:
        output_dir.mkdir(parents=True, exist_ok=True)

    pdf = fitz.open(pdf_path)
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
                    course_name = header["CourseName"]
                    university_name = header["UniversityName"]

                    fact_rows.append(
                        {
                            "AcademicYear": ACADEMIC_YEAR,
                            "ExamYear": EXAM_YEAR,
                            "PublicationDate": PUBLICATION_DATE,
                            "CourseID": make_id("COURSE", course_name),
                            "CourseName": course_name,
                            "UniversityID": make_id("UNIVERSITY", university_name),
                            "UniversityName": university_name,
                            "DistrictID": district_id,
                            "DistrictName": district_name,
                            "CutoffZ": cutoff_z,
                            "CutoffStatus": cutoff_status,
                            "AllIslandMerit": header["AllIslandMerit"],
                            "AptitudeTest": header["AptitudeTest"],
                            "Page": page_number,
                            "SourceFile": pdf_path.name,
                        }
                    )

    fact = pd.DataFrame(fact_rows)

    course_dim = (
        fact[["CourseID", "CourseName"]]
        .drop_duplicates()
        .sort_values("CourseName")
        .reset_index(drop=True)
    )
    university_dim = (
        fact[["UniversityID", "UniversityName"]]
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
                "YearID": "YEAR_2025_2026",
                "AcademicYear": ACADEMIC_YEAR,
                "ExamYear": EXAM_YEAR,
                "PublicationDate": PUBLICATION_DATE,
            }
        ]
    )

    fact_columns = [
        "AcademicYear", "ExamYear", "PublicationDate",
        "CourseID", "CourseName",
        "UniversityID", "UniversityName",
        "DistrictID", "DistrictName",
        "CutoffZ", "CutoffStatus",
        "AllIslandMerit", "AptitudeTest",
        "Page", "SourceFile",
    ]
    fact = fact[fact_columns]
    fact = fact.sort_values(["CourseName", "UniversityName", "DistrictName"]).reset_index(drop=True)

    if write_csv:
        fact.to_csv(output_dir / "fact_cutoffs.csv", index=False, encoding="utf-8-sig")
        course_dim.to_csv(output_dir / "dim_course.csv", index=False, encoding="utf-8-sig")
        university_dim.to_csv(output_dir / "dim_university.csv", index=False, encoding="utf-8-sig")
        district_dim.to_csv(output_dir / "dim_district.csv", index=False, encoding="utf-8-sig")
        year_dim.to_csv(output_dir / "dim_year.csv", index=False, encoding="utf-8-sig")

    report_lines = [
        "Sri Lanka A/L UGC cutoff extraction validation",
        f"Source: {pdf_path.name}",
        f"Academic year: {ACADEMIC_YEAR}",
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
