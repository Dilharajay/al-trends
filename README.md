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
│   ├── api/                 # Production FastAPI REST API
│   │   ├── main.py          # API entrypoint, CORS, slowapi rate-limiting & static app mount
│   │   ├── schemas.py       # Pydantic v2 data contracts
│   │   └── service.py       # In-memory cached model inference & student evaluation
│   ├── web/                 # Modern, zero-build deployable Web Frontend (HTML5/Tailwind/Chart.js)
│   │   ├── index.html       # Single Page Application
│   │   ├── app.js           # Client-side API integration, telemetry & Chart.js rendering
│   │   └── style.css        # Custom styles and status badges
│   ├── assets/              # Dagster Software-Defined Assets (SDA)
│   │   ├── core.py          # Bronze extraction, combinations, and star schema denormalization
│   │   └── ml.py            # Feature engineering and temporal-split Random Forest training
│   ├── validator/           # UGC Declarative Rules Engine
│   │   └── engine.py        # Stream validation logic and automatic single-subject swaps
│   ├── zscore_extractor/    # Multi-year PDF parsing engine
│   ├── generate_combinations.py # Dynamically generates dim_combination using the validator
│   ├── generate_bridge.py   # Vectorized course-to-combination mapping
│   ├── dashboard.py         # Direct-database Streamlit analytics app
│   ├── api_dashboard.py     # API-powered Streamlit dashboard
│   └── definitions.py       # Dagster definitions entrypoint
├── notebooks/               
│   ├── 01_exploratory_data_analysis.ipynb # Historical cutoff distributions & trends
│   ├── 02_data_quality_investigation.ipynb # Extraction robustness & NQC cell verification
│   └── 03_machine_learning_pipeline.ipynb # End-to-end ML training, diagnostics & inference
├── tests/
│   ├── test_api.py          # Unit tests for FastAPI endpoints, rate-limiter, and static mount
│   └── test_validator.py    # Unit tests for the UGC stream combination engine
├── data/                    # Raw PDFs and bronze SQLite/Parquet/CSV star schema tables
├── models/                  # Pickled ML models (rf_model.pkl) and encoders (encoders.pkl)
└── docs/                    # Academic report, data dictionary, layout guide, presentation script
```

## Quick Start

### 1. Install Dependencies
This project uses `uv` for fast dependency management:
```bash
uv sync
```

### 2. Run the End-to-End Dagster Pipeline
Materialize all Dagster assets (extraction, bridging, combinations, data quality checks, and ML training):
```bash
uv run dagster asset materialize --select "*" -f src/definitions.py
```
Or start the Dagster UI to inspect asset lineage:
```bash
uv run dagster dev -f src/definitions.py
```

### 3. Run Automated Tests
Execute the full test suite (15 unit tests covering the API, rate limiter, static frontend, and UGC validator):
```bash
uv run pytest tests/
```

### 4. Launch the Web Application & REST API
A single command launches the production FastAPI server, which hosts **both** the interactive REST API and the web frontend:
```bash
uv run uvicorn src.api.main:app --reload --port 8000
```
Once started, access:
- 🌐 **Web Frontend (No Streamlit required)**: [http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/) (or simply [http://127.0.0.1:8000/](http://127.0.0.1:8000/))
- 📄 **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📚 **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 5. (Optional) Run Streamlit Dashboards
If preferred, launch the legacy direct-database dashboard or the API-powered Streamlit client:
```bash
# API-powered Streamlit client
uv run streamlit run src/api_dashboard.py

# Direct SQLite database dashboard
uv run streamlit run src/dashboard.py
```

### 6. Interactive Exploratory & Machine Learning Notebooks
- `notebooks/01_exploratory_data_analysis.ipynb`: Initial EDA on historical cutoffs and intake capacity.
- `notebooks/02_data_quality_investigation.ipynb`: Deep dive into extraction robustness and missing `NQC` handling.
- `notebooks/03_machine_learning_pipeline.ipynb`: End-to-end ML benchmark, residual diagnostics, and inference simulation.

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

## Docker Containerization & Cloud Deployment

The application is fully containerized using a multi-stage `Dockerfile` and automated through **Docker Hub**:

- **Docker Hub Repository**: [`dilhara0592/image-test`](https://hub.docker.com/r/dilhara0592/image-test)
- **GitHub Actions CI/CD Workflow**: [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml) (runs unit tests, builds container, and pushes `dilhara0592/image-test:latest` to Docker Hub)
- **Cloud Configurations**: Ready-to-deploy blueprints for **Render** ([`render.yaml`](render.yaml)), **Railway** ([`railway.toml`](railway.toml)), **Google Cloud Run**, and **AWS App Runner**.
- **Detailed Guide**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step cloud deployment instructions.

### Run with Docker locally:
```bash
docker build -t dilhara0592/image-test:latest .
docker run -p 8000:8000 dilhara0592/image-test:latest
# Or run with docker-compose:
docker compose up --build
```
