import pandas as pd
from pathlib import Path
from dagster import asset

from src.zscore_extractor.cli import run_batch
from src.generate_combinations import generate_combinations
from src.generate_bridge import generate_bridge

@asset
def extracted_bronze_data() -> None:
    """Extracts PDF cutoffs and writes to bronze storage (CSV/Parquet/SQLite)."""
    input_dir = Path("data/raw")
    output_base = Path("data/bronze")
    db_path = Path("data/bronze/db/al_cutoffs.db")
    run_batch(
        input_dir=input_dir,
        output_base=output_base,
        db_path=db_path,
        use_db=True,
        overwrite_db=True,
    )

@asset(deps=[extracted_bronze_data])
def dim_combination() -> None:
    """Generates the mathematically exhaustive valid UGC subject combinations."""
    generate_combinations()

@asset(deps=[extracted_bronze_data, dim_combination])
def bridge_course_combination() -> None:
    """Maps courses to valid combinations based on heuristic rules."""
    generate_bridge()

@asset(deps=[bridge_course_combination])
def denormalized_fact_data() -> pd.DataFrame:
    """Loads dimension tables and merges them with fact_cutoffs for downstream ML pipelines."""
    fact_df = pd.read_csv("data/bronze/csv/fact_cutoffs.csv")
    dim_course = pd.read_csv("data/bronze/csv/dim_course.csv")
    dim_uni = pd.read_csv("data/bronze/csv/dim_university.csv")
    dim_dist = pd.read_csv("data/bronze/csv/dim_district.csv")
    dim_year = pd.read_csv("data/bronze/csv/dim_year.csv")
    
    df = fact_df.merge(dim_course, on="CourseID", how="left")
    df = df.merge(dim_uni, on="UniversityID", how="left")
    df = df.merge(dim_dist, on="DistrictID", how="left")
    df = df.merge(dim_year, on="YearID", how="left")
    
    return df
