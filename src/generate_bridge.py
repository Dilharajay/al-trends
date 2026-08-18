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
    
    bridge_records = []
    
    # Simple heuristic rules to map course names to A/L streams
    for _, row in courses_df.iterrows():
        name_lower = row["CourseName"].lower()
        course_id = row["CourseID"]
        mapped_streams = set()
        
        # Heuristics for Biological Science
        if any(kw in name_lower for kw in ["medicine", "dental", "veterinary", "biology", "zoology", "botany", "ayurveda", "nursing", "pharmacy", "medical", "biomedical"]):
            mapped_streams.add("Biological Science")
            
        # Heuristics for Physical Science
        if any(kw in name_lower for kw in ["engineering", "physical science", "physics", "mathematics", "computer science", "architecture", "surveying", "quantity surveying"]):
            # Note: Engineering Technology is a different stream
            if "technology" not in name_lower or "computer" in name_lower:
                mapped_streams.add("Physical Science")
                
        # Heuristics for Commerce
        if any(kw in name_lower for kw in ["commerce", "management", "business", "accounting", "finance", "estate management"]):
            mapped_streams.add("Commerce")
            
        # Heuristics for Arts
        if any(kw in name_lower for kw in ["arts", "law", "languages", "translation", "social", "teaching", "education", "design", "music", "dance", "drama"]):
            mapped_streams.add("Arts")
            
        # Heuristics for Technology
        if any(kw in name_lower for kw in ["engineering technology", "bio systems technology", "information and communication technology", "biosystems"]):
            mapped_streams.add("Technology")
            
        # Information Technology (Often flexible, let's map to PHY and TEC for stubbing)
        if "information technology" in name_lower and "communication" not in name_lower:
            mapped_streams.add("Physical Science")
            mapped_streams.add("Technology")
            
        # If no heuristic matched, fallback to a flexible stream or mark for review
        # For stubbing purposes, we'll assign them to Arts as it is the most flexible, or just Physical/Bio if it sounds sciency
        if not mapped_streams:
            if "science" in name_lower:
                mapped_streams.update(["Physical Science", "Biological Science"])
            else:
                mapped_streams.add("Arts")
                
        # Create bridge records for all combinations in the mapped streams
        for stream in mapped_streams:
            if stream in stream_combinations:
                for combo_id in stream_combinations[stream]:
                    bridge_records.append({
                        "CourseID": course_id,
                        "combination_id": combo_id
                    })
                    
    bridge_df = pd.DataFrame(bridge_records).drop_duplicates()
    
    # Save outputs
    csv_dir = Path("data/bronze/csv")
    parquet_dir = Path("data/bronze/parquet")
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    
    bridge_df.to_csv(csv_dir / "bridge_course_combination.csv", index=False, encoding="utf-8-sig")
    bridge_df.to_parquet(parquet_dir / "bridge_course_combination.parquet", index=False)
    
    bridge_df.to_sql("bridge_course_combination", conn, if_exists="replace", index=False)
    conn.close()
    
    print(f"bridge_course_combination generated with {len(bridge_df)} records mapping {len(courses_df)} courses.")

if __name__ == "__main__":
    generate_bridge()
