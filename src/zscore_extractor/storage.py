from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def write_tables_to_sqlite(
    db_path: Path,
    fact: pd.DataFrame,
    course_dim: pd.DataFrame,
    university_dim: pd.DataFrame,
    district_dim: pd.DataFrame,
    year_dim: pd.DataFrame,
    intake_fact: pd.DataFrame,
    overwrite: bool = True,
) -> None:
    """Create schema and write tables into a SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite and db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS dim_course (
            CourseID TEXT PRIMARY KEY,
            CourseName TEXT
        );
        CREATE TABLE IF NOT EXISTS dim_university (
            UniversityID TEXT PRIMARY KEY,
            UniversityName TEXT
        );
        CREATE TABLE IF NOT EXISTS dim_district (
            DistrictID TEXT PRIMARY KEY,
            DistrictName TEXT
        );
        CREATE TABLE IF NOT EXISTS dim_year (
            YearID TEXT PRIMARY KEY,
            AcademicYear TEXT,
            ExamYear INTEGER,
            PublicationDate TEXT
        );
        CREATE TABLE IF NOT EXISTS fact_cutoffs (
            AcademicYear TEXT,
            ExamYear INTEGER,
            PublicationDate TEXT,
            CourseID TEXT,
            CourseName TEXT,
            UniversityID TEXT,
            UniversityName TEXT,
            DistrictID TEXT,
            DistrictName TEXT,
            CutoffZ REAL,
            CutoffStatus TEXT,
            AllIslandMerit BOOLEAN,
            AptitudeTest BOOLEAN,
            Page INTEGER,
            SourceFile TEXT
        );
        CREATE TABLE IF NOT EXISTS fact_course_intake (
            AcademicYear TEXT,
            CourseID TEXT,
            Intake INTEGER
        );
        """
    )

    if overwrite:
        cur.execute("DELETE FROM dim_course")
        cur.execute("DELETE FROM dim_university")
        cur.execute("DELETE FROM dim_district")
        cur.execute("DELETE FROM dim_year")
        cur.execute("DELETE FROM fact_cutoffs")
        cur.execute("DELETE FROM fact_course_intake")

    cur.executemany(
        "INSERT OR IGNORE INTO dim_course (CourseID, CourseName) VALUES (?, ?)",
        [(row["CourseID"], row["CourseName"]) for _, row in course_dim.iterrows()],
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dim_university (UniversityID, UniversityName) VALUES (?, ?)",
        [(row["UniversityID"], row["UniversityName"]) for _, row in university_dim.iterrows()],
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dim_district (DistrictID, DistrictName) VALUES (?, ?)",
        [(row["DistrictID"], row["DistrictName"]) for _, row in district_dim.iterrows()],
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dim_year (YearID, AcademicYear, ExamYear, PublicationDate) VALUES (?, ?, ?, ?)",
        [
            (row["YearID"], row["AcademicYear"], int(row["ExamYear"]), row["PublicationDate"]) for _, row in year_dim.iterrows()
        ],
    )

    fact.to_sql("fact_cutoffs", conn, if_exists="append", index=False)
    intake_fact.to_sql("fact_course_intake", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def write_combined_outputs(output_base: Path, fact: pd.DataFrame, course_dim: pd.DataFrame, university_dim: pd.DataFrame, district_dim: pd.DataFrame, year_dim: pd.DataFrame, intake_fact: pd.DataFrame) -> None:
    output_base.mkdir(parents=True, exist_ok=True)

    csv_dir = output_base / "csv"
    parquet_dir = output_base / "parquet"
    csv_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)

    fact.to_csv(csv_dir / "fact_cutoffs.csv", index=False, encoding="utf-8-sig")
    course_dim.to_csv(csv_dir / "dim_course.csv", index=False, encoding="utf-8-sig")
    university_dim.to_csv(csv_dir / "dim_university.csv", index=False, encoding="utf-8-sig")
    district_dim.to_csv(csv_dir / "dim_district.csv", index=False, encoding="utf-8-sig")
    year_dim.to_csv(csv_dir / "dim_year.csv", index=False, encoding="utf-8-sig")
    intake_fact.to_csv(csv_dir / "fact_course_intake.csv", index=False, encoding="utf-8-sig")

    for name, df in {
        "fact_cutoffs": fact,
        "dim_course": course_dim,
        "dim_university": university_dim,
        "dim_district": district_dim,
        "dim_year": year_dim,
        "fact_course_intake": intake_fact,
    }.items():
        df.to_parquet(parquet_dir / f"{name}.parquet", index=False)
