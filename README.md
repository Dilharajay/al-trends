# AL Trends

A modular Python project for extracting Sri Lankan GCE A/L university cutoff tables from PDF documents and consolidating them into a single storage layer.

This project reads PDFs from `data/raw`, parses the course/university cutoff tables, and writes a unified output set to `data/bronze` in separate folders:

- SQLite database: `db/al_cutoffs.db`
- combined CSVs: `csv/fact_cutoffs.csv`, `csv/dim_course.csv`, `csv/dim_university.csv`, `csv/dim_district.csv`, `csv/dim_year.csv`
- Parquet exports: `parquet/fact_cutoffs.parquet`, `parquet/dim_course.parquet`, `parquet/dim_university.parquet`, `parquet/dim_district.parquet`, `parquet/dim_year.parquet`

## Features

- Batch processing across all PDFs in `data/raw`
- Single consolidated schema for fact and dimension tables
- Writes to SQLite, CSV, and Parquet
- Handles newer and older PDF layouts with a tolerant extraction fallback
- Modular package layout for easier maintenance and extension

## Project structure

```text
src/
  zscore_extractor/
    __init__.py
    cli.py
    config.py
    extract_al_cutoffs.py
    main.py
    parsing.py
    storage.py

data/
  raw/
  bronze/
```

## Quick start

Install dependencies:

```bash
uv sync
```

Run the full batch pipeline:

```bash
uv run python3 src/zscore_extractor/extract_al_cutoffs.py -i data/raw -b data/bronze
```

This scans every PDF in `data/raw`, extracts cutoff data, writes one SQLite database, and exports combined CSV/Parquet files to `data/bronze`.

Single-PDF run:

```bash
uv run python3 src/zscore_extractor/extract_al_cutoffs.py data/raw/COP_2025_2026.pdf -o data/bronze/COP_2025_2026
```

Append instead of overwrite the database:

```bash
uv run python3 src/zscore_extractor/extract_al_cutoffs.py -i data/raw -b data/bronze --append-db
```

Skip SQLite output and just export CSV/Parquet:

```bash
uv run python3 src/zscore_extractor/extract_al_cutoffs.py -i data/raw -b data/bronze --no-db
```

## Data model

The pipeline produces these tables:

- `fact_cutoffs`
  - AcademicYear
  - ExamYear
  - PublicationDate
  - CourseID
  - CourseName
  - UniversityID
  - UniversityName
  - DistrictID
  - DistrictName
  - CutoffZ
  - CutoffStatus
  - AllIslandMerit
  - AptitudeTest
  - Page
  - SourceFile

Dimension tables:

- `dim_course`
- `dim_university`
- `dim_district`
- `dim_year`

## Notes

- The database is overwritten by default on each batch run.
- The extractor uses a tolerant parser for older PDF layouts that differ from the latest format.
- The generated output is intended for downstream analysis in tools such as Power BI, pandas, or DuckDB.

See also: [docs/POWERBI_SCHEMA_SUMMARY.md](docs/POWERBI_SCHEMA_SUMMARY.md)

## License

This project is for internal data extraction and analysis workflows related to Sri Lankan university admissions cutoff tables.
