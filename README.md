# AL Trends (Sri Lanka A/L Z-Score Prediction & Analysis)

An end-to-end MLOps project for extracting Sri Lankan GCE A/L university cutoff tables from official UGC PDF documents, dynamically validating subject combinations, and training machine learning models to predict university cutoffs.

## Project Architecture

This project is built using a highly modular, robust architecture powered by **Dagster**. The pipeline seamlessly executes the following stages as Software-Defined Assets:

1. **Extraction (`zscore_extractor`)**: Ingests raw UGC PDFs spanning multiple academic years, handles OCR and layout anomalies, and consolidates the data into structured SQLite/CSV/Parquet fact and dimension tables.
2. **UGC Stream Validation (`validator`)**: A powerful declarative rule engine that mathematically validates every possible 3-subject combination against official UGC circulars (Biological Science, Physical Science, Engineering Technology, Bio-systems Technology, Commerce, Arts). It dynamically discovers exactly 168 mathematically valid combinations.
3. **Bridge Generation**: Maps parsed university courses to eligible UGC streams using vectorized heuristics.
4. **Machine Learning (`mlops/steps`)**: Cleans data, applies deterministic `OrdinalEncoding`, enforces strict data quality checks, and trains a `RandomForestRegressor` model using a time-based split (preventing temporal data leakage) to predict future Z-score cutoffs.

All data artifacts are written using a **Write-Audit-Publish (WAP)** pattern to guarantee atomic writes and idempotent pipeline executions.

## Project Structure

```text
al-trends/
├── src/
│   ├── assets/              # Dagster Software-Defined Assets
│   │   ├── core.py          # Extraction and dimension tables
│   │   └── ml.py            # Feature engineering and model training
│   ├── validator/           # UGC Rules Engine
│   │   └── engine.py        # Stream validation logic and swap generation
│   ├── zscore_extractor/    # PDF Parsing engine
│   ├── generate_combinations.py # Dynamically generates dim_combination using the validator
│   ├── generate_bridge.py   # Vectorized course mapping
│   └── definitions.py       # Dagster definitions entrypoint
├── notebooks/               
│   └── data_quality_investigation.ipynb # Interactive EDA and DQ validation
├── tests/
│   └── test_validator.py    # Unit tests for the UGC stream engine
├── data/                    # Raw PDFs and Bronze extracted data
└── models/                  # Pickled ML models and encoders
```

## Quick Start

### 1. Install Dependencies
This project uses `uv` for lightning-fast dependency management:
```bash
uv sync
```

### 2. Run the End-to-End Pipeline
Materialize all Dagster assets (extraction, bridging, combinations, data quality checks, and ML training) directly from the command line:
```bash
uv run dagster asset materialize --select "*" -f src/definitions.py
```
Or start the Dagster UI to visualize the dependency graph and trigger the pipeline interactively:
```bash
uv run dagster dev -f src/definitions.py
```

### 3. Run Unit Tests
To verify the UGC combination rule engine against complex edge cases (e.g., disallowed pairs, barred technology subjects):
```bash
uv run pytest tests/test_validator.py
```

### 4. Interactive Data Quality Analysis
Explore the extraction robustness and view the distribution of legitimately missing `NQC` (Not Qualified for Course) cells:
Open `notebooks/data_quality_investigation.ipynb` in Jupyter or VS Code.

## The UGC Validator Engine

The project features a dedicated A/L subject combination validator (`src/validator/engine.py`) that strictly adheres to the UGC admission criteria. 

**Features:**
- **Prioritized Ruleset:** Walks through stream constraints in priority order (Bio → Phys → Eng Tech → Bio-systems Tech → Commerce → Arts).
- **Hard Constraints:** Enforces disallowed pairs (e.g., Biology + Combined Mathematics is strictly banned).
- **Technology Open Baskets:** Properly enforces the "barred 3rd subject" rules for technology streams.
- **Auto-Swaps:** When an invalid combination is tested, the engine computes single-subject swaps to recommend how the combination can be made valid.

## Data Model

The pipeline extracts and structures the data into a star schema optimized for BI tools (like Power BI) and ML engineering:
- `fact_cutoffs`: The central fact table (Z-Scores by Course, Uni, District, Year)
- `dim_course`: Unique university degree programs
- `dim_university`: Standardized university names
- `dim_district`: The 25 administrative districts
- `dim_year`: Academic and Examination year mapping
- `dim_combination`: The 168 dynamically discovered valid UGC subject combinations
- `bridge_course_combination`: Many-to-many bridge table linking courses to eligible A/L combinations

## Reliability Features

- **Write-Audit-Publish (WAP)**: Data is written to temporary files, strictly audited (e.g., null checks, row counts), and then atomically swapped into production.
- **Data Quality Alerts**: The pipeline asserts that no more than 25% of cutoff values are missing (accounting for normal NQC cells), failing fast if data drift occurs.
- **Time-Based ML Splitting**: ML models are trained strictly on past data and evaluated on the latest year to mimic true production serving and avoid temporal leakage.
