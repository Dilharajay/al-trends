from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .parsing import extract_pdf
from .storage import write_combined_outputs, write_tables_to_sqlite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract UGC Sri Lankan A/L admission cutoff tables.")
    parser.add_argument("pdf", type=Path, nargs="?", default=None, help="Path to a specific UGC PDF. If omitted, batch mode scans `--input-dir`.")
    parser.add_argument("-i", "--input-dir", type=Path, default=Path("data/raw"), help="Directory with PDFs to ingest.")
    parser.add_argument("-b", "--output-base", type=Path, default=Path("data/bronze"), help="Output directory for batch CSV/Parquet outputs.")
    parser.add_argument("-o", "--output", type=Path, default=Path("al_cutoff_data"), help="Output directory for single-PDF runs.")
    parser.add_argument("--db", type=Path, default=Path("data/bronze/al_cutoffs.db"), help="SQLite database path.")
    parser.add_argument("--no-db", action="store_true", help="Skip SQLite output.")
    parser.add_argument("--append-db", action="store_true", help="Append to the database instead of overwriting it.")
    return parser


def run_batch(input_dir: Path, output_base: Path, db_path: Path, use_db: bool, overwrite_db: bool) -> None:
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {input_dir}")

    fact_dfs = []
    course_dims = []
    university_dims = []
    district_dims = []
    year_dims = []

    for pdf_path in pdf_files:
        out_dir = output_base / pdf_path.stem
        print(f"\nProcessing {pdf_path.name} -> {out_dir}")
        try:
            fact, course_dim, university_dim, district_dim, year_dim = extract_pdf(pdf_path, out_dir, write_csv=False)
        except Exception as exc:
            print(f"Error extracting {pdf_path.name}: {exc}")
            print("Skipping this file and continuing with the next one.")
            continue

        fact_dfs.append(fact)
        course_dims.append(course_dim)
        university_dims.append(university_dim)
        district_dims.append(district_dim)
        year_dims.append(year_dim)

    if not fact_dfs:
        print("No successful extractions; nothing to write.")
        return

    all_fact = pd.concat(fact_dfs, ignore_index=True)
    all_course = pd.concat(course_dims, ignore_index=True).drop_duplicates(subset=["CourseID"]).reset_index(drop=True)
    all_university = pd.concat(university_dims, ignore_index=True).drop_duplicates(subset=["UniversityID"]).reset_index(drop=True)
    all_district = district_dims[0]
    all_year = pd.concat(year_dims, ignore_index=True).drop_duplicates(subset=["YearID"]).reset_index(drop=True)

    if use_db:
        print(f"Writing aggregated data to DB: {db_path} (overwrite={overwrite_db})")
        write_tables_to_sqlite(db_path, all_fact, all_course, all_university, all_district, all_year, overwrite=overwrite_db)

    write_combined_outputs(output_base, all_fact, all_course, all_university, all_district, all_year)
    print(f"Combined CSVs and Parquet files written to: {output_base.resolve()}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.pdf:
        if not args.pdf.exists() or not args.pdf.is_file():
            raise FileNotFoundError(f"PDF not found: {args.pdf}")
        extract_pdf(args.pdf, args.output)
        return

    run_batch(
        input_dir=args.input_dir,
        output_base=args.output_base,
        db_path=args.db,
        use_db=not args.no_db,
        overwrite_db=not args.append_db,
    )


if __name__ == "__main__":
    main()
