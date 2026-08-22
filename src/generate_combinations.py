import pandas as pd
import sqlite3
import sys
import itertools
from pathlib import Path

# Add project root to path so we can import from src if run directly
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.validator.engine import ALL_SUBJECTS, validateCombination

def generate_combinations():
    combinations = []
    stream_counters = {}
    
    # Generate every mathematically possible 3-subject combination
    for combo in itertools.combinations(ALL_SUBJECTS, 3):
        combo_list = list(combo)
        # Check against UGC rules
        streams, _, _ = validateCombination(combo_list, with_swaps=False)
        
        for stream in streams:
            if stream not in stream_counters:
                stream_counters[stream] = 1
                
            prefix = stream.split()[0].upper()[:3]
            if stream == "Engineering Technology": prefix = "ENG"
            if stream == "Bio-systems Technology": prefix = "BST"
            
            combo_id = f"{prefix}-{stream_counters[stream]:03d}"
            stream_counters[stream] += 1
            
            combinations.append({
                "combination_id": combo_id,
                "stream": stream,
                "subject_1": combo_list[0],
                "subject_2": combo_list[1],
                "subject_3": combo_list[2]
            })
            
    df = pd.DataFrame(combinations)
    # Sort for deterministic output
    df = df.sort_values(by=["stream", "subject_1", "subject_2", "subject_3"]).reset_index(drop=True)
    
    # Re-assign sequential IDs after sorting
    df['combination_id'] = df.groupby('stream').cumcount() + 1
    
    def format_id(row):
        prefix = row['stream'].split()[0].upper()[:3]
        if row['stream'] == "Engineering Technology": prefix = "ENG"
        if row['stream'] == "Bio-systems Technology": prefix = "BST"
        return f"{prefix}-{row['combination_id']:03d}"
        
    df['combination_id'] = df.apply(format_id, axis=1)
    
    csv_dir = Path("data/bronze/csv")
    parquet_dir = Path("data/bronze/parquet")
    db_path = Path("data/bronze/db/al_cutoffs.db")
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    
    temp_csv = csv_dir / "dim_combination_tmp.csv"
    temp_parquet = parquet_dir / "dim_combination_tmp.parquet"
    
    # Write
    df.to_csv(temp_csv, index=False, encoding="utf-8-sig")
    df.to_parquet(temp_parquet, index=False)
    
    # Audit
    assert len(df) > 0, "Data Quality Error: No combination records generated!"
    assert not df.isnull().any().any(), "Data Quality Error: Nulls found in combinations!"
    
    # Publish (Atomic swap)
    temp_csv.replace(csv_dir / "dim_combination.csv")
    temp_parquet.replace(parquet_dir / "dim_combination.parquet")
    
    # DB WAP Publish
    conn = sqlite3.connect(db_path)
    temp_table = "dim_combination_tmp"
    final_table = "dim_combination"
    df.to_sql(temp_table, conn, if_exists="replace", index=False)
    
    conn.execute("BEGIN TRANSACTION")
    conn.execute(f"DROP TABLE IF EXISTS {final_table}")
    conn.execute(f"ALTER TABLE {temp_table} RENAME TO {final_table}")
    conn.commit()
    conn.close()
    
    print("dim_combination generated and saved to csv, parquet, and sqlite.")

if __name__ == "__main__":
    generate_combinations()
