import pandas as pd
import sqlite3
from pathlib import Path

def generate_bridge():
    db_path = Path("data/bronze/db/al_cutoffs.db")
    conn = sqlite3.connect(db_path)
    
    # Load all courses
    courses_df = pd.read_sql("SELECT CourseID, CourseName FROM dim_course", conn)
    
    # Load combinations to get the IDs
    combinations_df = pd.read_sql("SELECT combination_id, stream FROM dim_combination", conn)
    
    # Group combination IDs by stream for easy mapping
    stream_combinations = combinations_df.groupby("stream")["combination_id"].apply(list).to_dict()
    
    # Vectorized heuristic rules to map course names to A/L streams
    courses_df['name_lower'] = courses_df['CourseName'].str.lower()
    
    bio_kws = "medicine|dental|veterinary|biology|zoology|botany|ayurveda|nursing|pharmacy|medical|biomedical"
    phy_kws = "engineering|physical science|physics|mathematics|computer science|architecture|surveying|quantity surveying"
    com_kws = "commerce|management|business|accounting|finance|estate management"
    art_kws = "arts|law|languages|translation|social|teaching|education|design|music|dance|drama"
    tech_kws = "engineering technology|bio systems technology|information and communication technology|biosystems"
    
    courses_df['is_bio'] = courses_df['name_lower'].str.contains(bio_kws, regex=True, na=False)
    
    phy_base = courses_df['name_lower'].str.contains(phy_kws, regex=True, na=False)
    tech_exclude = courses_df['name_lower'].str.contains("technology", regex=True, na=False)
    comp_include = courses_df['name_lower'].str.contains("computer", regex=True, na=False)
    courses_df['is_phy'] = phy_base & (~tech_exclude | comp_include)
    
    courses_df['is_com'] = courses_df['name_lower'].str.contains(com_kws, regex=True, na=False)
    courses_df['is_art'] = courses_df['name_lower'].str.contains(art_kws, regex=True, na=False)
    courses_df['is_tech'] = courses_df['name_lower'].str.contains(tech_kws, regex=True, na=False)
    
    it_base = courses_df['name_lower'].str.contains("information technology", regex=True, na=False)
    comm_exclude = courses_df['name_lower'].str.contains("communication", regex=True, na=False)
    is_it = it_base & ~comm_exclude
    
    courses_df.loc[is_it, 'is_phy'] = True
    courses_df.loc[is_it, 'is_tech'] = True
    
    any_mapped = courses_df[['is_bio', 'is_phy', 'is_com', 'is_art', 'is_tech']].any(axis=1)
    unmapped = ~any_mapped
    is_science = courses_df['name_lower'].str.contains("science", regex=True, na=False)
    
    courses_df.loc[unmapped & is_science, 'is_phy'] = True
    courses_df.loc[unmapped & is_science, 'is_bio'] = True
    courses_df.loc[unmapped & ~is_science, 'is_art'] = True
    
    stream_map = {
        'Biological Science': 'is_bio',
        'Physical Science': 'is_phy',
        'Commerce': 'is_com',
        'Arts': 'is_art',
        'Engineering Technology': 'is_tech',
        'Bio-systems Technology': 'is_tech'
    }
    
    melted = courses_df.melt(id_vars=['CourseID'], value_vars=list(stream_map.values()), var_name='stream_col', value_name='is_mapped')
    mapped_streams_df = melted[melted['is_mapped']].copy()
    
    inv_stream_map = {v: k for k, v in stream_map.items()}
    mapped_streams_df['stream'] = mapped_streams_df['stream_col'].map(inv_stream_map)
    
    combo_expanded = [{'stream': stream, 'combination_id': cid} for stream, combo_ids in stream_combinations.items() for cid in combo_ids]
    combo_df = pd.DataFrame(combo_expanded)
    
    bridge_df = pd.merge(mapped_streams_df[['CourseID', 'stream']], combo_df, on='stream', how='inner')
    bridge_df = bridge_df[['CourseID', 'combination_id']].drop_duplicates()
    
    # Save outputs (Write-Audit-Publish pattern)
    csv_dir = Path("data/bronze/csv")
    parquet_dir = Path("data/bronze/parquet")
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    
    temp_csv = csv_dir / "bridge_course_combination_tmp.csv"
    temp_parquet = parquet_dir / "bridge_course_combination_tmp.parquet"
    
    # Write
    bridge_df.to_csv(temp_csv, index=False, encoding="utf-8-sig")
    bridge_df.to_parquet(temp_parquet, index=False)
    
    # Audit
    assert len(bridge_df) > 0, "Data Quality Error: No bridge records generated!"
    assert not bridge_df.isnull().any().any(), "Data Quality Error: Nulls found in bridge records!"
    
    # Publish (Atomic swap)
    temp_csv.replace(csv_dir / "bridge_course_combination.csv")
    temp_parquet.replace(parquet_dir / "bridge_course_combination.parquet")
    
    # DB WAP Publish
    temp_table = "bridge_course_combination_tmp"
    final_table = "bridge_course_combination"
    bridge_df.to_sql(temp_table, conn, if_exists="replace", index=False)
    
    conn.execute("BEGIN TRANSACTION")
    conn.execute(f"DROP TABLE IF EXISTS {final_table}")
    conn.execute(f"ALTER TABLE {temp_table} RENAME TO {final_table}")
    conn.commit()
    conn.close()
    
    print(f"bridge_course_combination generated with {len(bridge_df)} records mapping {len(courses_df)} courses.")

if __name__ == "__main__":
    generate_bridge()
