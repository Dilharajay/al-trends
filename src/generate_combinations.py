import pandas as pd
import sqlite3
from pathlib import Path

def generate_combinations():
    combinations = [
        {"combination_id": "PHY-001", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Physics", "subject_3": "Chemistry"},
        {"combination_id": "PHY-002", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Physics", "subject_3": "ICT"},
        {"combination_id": "PHY-003", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Chemistry", "subject_3": "ICT"},
        {"combination_id": "PHY-004", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Physics", "subject_3": "Agricultural Science"},
        {"combination_id": "PHY-005", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Physics", "subject_3": "Statistics"},
        {"combination_id": "PHY-006", "stream": "Physical Science", "subject_1": "Combined Mathematics", "subject_2": "Chemistry", "subject_3": "Biology"},
        {"combination_id": "BIO-001", "stream": "Biological Science", "subject_1": "Biology", "subject_2": "Chemistry", "subject_3": "Physics"},
        {"combination_id": "BIO-002", "stream": "Biological Science", "subject_1": "Biology", "subject_2": "Chemistry", "subject_3": "Agricultural Science"},
        {"combination_id": "BIO-003", "stream": "Biological Science", "subject_1": "Biology", "subject_2": "Chemistry", "subject_3": "ICT"},
        {"combination_id": "BIO-004", "stream": "Biological Science", "subject_1": "Biology", "subject_2": "Physics", "subject_3": "Agricultural Science"},
        {"combination_id": "COM-001", "stream": "Commerce", "subject_1": "Accounting", "subject_2": "Business Studies", "subject_3": "Economics"},
        {"combination_id": "COM-002", "stream": "Commerce", "subject_1": "Accounting", "subject_2": "Business Studies", "subject_3": "ICT"},
        {"combination_id": "COM-003", "stream": "Commerce", "subject_1": "Accounting", "subject_2": "Economics", "subject_3": "Business Statistics"},
        {"combination_id": "COM-004", "stream": "Commerce", "subject_1": "Accounting", "subject_2": "Economics", "subject_3": "ICT"},
        {"combination_id": "COM-005", "stream": "Commerce", "subject_1": "Business Studies", "subject_2": "Economics", "subject_3": "ICT"},
        {"combination_id": "TEC-001", "stream": "Technology", "subject_1": "Engineering Technology", "subject_2": "Science for Technology", "subject_3": "ICT"},
        {"combination_id": "TEC-002", "stream": "Technology", "subject_1": "Engineering Technology", "subject_2": "Science for Technology", "subject_3": "Economics"},
        {"combination_id": "TEC-003", "stream": "Technology", "subject_1": "Engineering Technology", "subject_2": "Science for Technology", "subject_3": "Accounting"},
        {"combination_id": "TEC-004", "stream": "Technology", "subject_1": "Bio Systems Technology", "subject_2": "Science for Technology", "subject_3": "Agricultural Science"},
        {"combination_id": "TEC-005", "stream": "Technology", "subject_1": "Bio Systems Technology", "subject_2": "Science for Technology", "subject_3": "ICT"},
        {"combination_id": "TEC-006", "stream": "Technology", "subject_1": "Bio Systems Technology", "subject_2": "Science for Technology", "subject_3": "Economics"},
        {"combination_id": "ART-001", "stream": "Arts", "subject_1": "Political Science", "subject_2": "History", "subject_3": "Geography"},
        {"combination_id": "ART-002", "stream": "Arts", "subject_1": "Economics", "subject_2": "Political Science", "subject_3": "Geography"},
        {"combination_id": "ART-003", "stream": "Arts", "subject_1": "Logic & Scientific Method", "subject_2": "History", "subject_3": "English Literature"},
    ]
    
    df = pd.DataFrame(combinations)
    
    csv_dir = Path("data/bronze/csv")
    parquet_dir = Path("data/bronze/parquet")
    db_path = Path("data/bronze/db/al_cutoffs.db")
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(csv_dir / "dim_combination.csv", index=False, encoding="utf-8-sig")
    df.to_parquet(parquet_dir / "dim_combination.parquet", index=False)
    
    conn = sqlite3.connect(db_path)
    df.to_sql("dim_combination", conn, if_exists="replace", index=False)
    conn.close()
    
    print("dim_combination generated and saved to csv, parquet, and sqlite.")

if __name__ == "__main__":
    generate_combinations()
