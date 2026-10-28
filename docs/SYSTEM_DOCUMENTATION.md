# Technical system documentation: Sri Lanka A/L cutoff analysis and prediction platform

## Project overview

The Sri Lanka Advanced Level (A/L) Cutoff Analysis platform is an end-to-end data engineering and applied machine learning system. It ingests official University Grants Commission (UGC) admission cutoffs published as unstructured PDF documents, extracts and structures the data into a star schema data warehouse, validates secondary school subject combinations against UGC circular regulations, trains predictive models for university entrance marks, and serves predictions through an authenticated, containerized web service.

The platform addresses a structural information barrier in the Sri Lankan state university entrance process. Annually, the UGC publishes minimum qualifying Z-scores across 25 administrative districts for over 100 undergraduate degree courses across 17 state universities. Because these cutoff marks are distributed exclusively in static PDF format, students and educators struggle to analyze multi-year admission trends, examine district quota disparities, or anticipate competitive cutoff shifts. This platform automates data extraction, formalizes admission rules into an algorithmic validator, and provides machine-learning-assisted cutoff forecasting.

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion & Transformation"]
        A["Raw UGC PDFs (2018-2026)"] --> B["Spatial Text Extraction (PyMuPDF)"]
        B --> C["Data Cleaning & NQC Standardization"]
        C --> D["Dagster Software-Defined Assets"]
        D --> E["Star Schema Warehouse (SQLite / Parquet)"]
    end

    subgraph Validation ["2. Rules Engine"]
        F["UGC Circular Regulations"] --> G["Combinations Engine"]
        G --> H["168 Valid Subject Combinations"]
        H --> I["Vectorized Course Bridge Table"]
    end

    subgraph MachineLearning ["3. Machine Learning Pipeline"]
        E --> J["Temporal Split (Train < Max Year)"]
        J --> K["RandomForestRegressor Training"]
        K --> L["Lossless zlib Compression (Joblib Level 6)"]
        L --> M["Persisted Model: rf_model.pkl (55.7 MB)"]
    end

    subgraph Serving ["4. Containerized Serving"]
        M --> N["FastAPI Application Server"]
        E --> N
        I --> N
        O["React 18 SPA (Vite / Tailwind)"] --> N
        N --> P["Docker Multi-Stage Build"]
        P --> Q["Docker Hub: dilhara0592/image-test"]
        Q --> R["Cloud Runtimes (Render / Cloud Run / Railway)"]
    end
```

## Data engineering pipeline

### PDF extraction and spatial parsing

The extraction engine parses raw UGC admission handbooks and cutoff publications covering academic years from 2018/2019 through 2025/2026. These source documents present several extraction challenges:

1. Tables are rendered in landscape orientation with irregular column boundaries and overlapping table cells.
2. Degree titles and university identifiers vary in spelling across publication cycles.
3. Selective districts contain "NQC" (No Qualified Candidates) entries where no applicant met the minimum threshold for that course.

The parser uses `pymupdf` to capture bounding boxes for character tokens on each page. Tokens are grouped into horizontal row bands based on vertical coordinate thresholds. Columns are determined by clustering the horizontal positions of table header boundaries. Cells containing "NQC" are preserved as discrete non-numeric statuses rather than converted to zeros, preventing mathematical bias in downstream statistical aggregates.

All university and program strings are reconciled against a canonical UGC codebook (`UNICODES.pdf`), assigning persistent numeric keys (`CourseID`, `UniversityID`, `DistrictID`).

### Data warehouse star schema

The extracted records are organized into a dimensional model optimized for query performance in analytical tools and low-latency API retrieval:

- `fact_cutoffs`: Measures minimum qualifying Z-scores, recording `CutoffID`, `CourseID`, `UniversityID`, `DistrictID`, `YearID`, and `CutoffZ`.
- `fact_course_intake`: Measures university intake capacity, linking courses and universities to planned undergraduate seat allocations.
- `dim_course`: Standardized undergraduate degree programs (e.g., Medicine, Engineering, Computer Science).
- `dim_university`: State universities operating under UGC purview.
- `dim_district`: The 25 official administrative districts of Sri Lanka.
- `dim_year`: Calendar exam years and corresponding academic admission years.
- `dim_combination`: The 168 mathematically valid three-subject combinations discovered by the validator engine.
- `bridge_course_combination`: Many-to-many relationship linking undergraduate courses to eligible A/L subject combinations.

### Asset orchestration and data quality

Pipeline workflows are defined as Dagster Software-Defined Assets (SDAs) in `src/assets/core.py`. Execution follows a Write-Audit-Publish (WAP) pattern:

1. Extracted data is written to isolated staging tables.
2. Automated audit rules verify schema contracts, verifying that null values in primary foreign keys remain at zero and checking that dropped rows from missing values do not exceed 25% of any batch.
3. Validated datasets are atomically moved to the production SQLite database (`data/bronze/db/al_cutoffs.db`) and Parquet stores.

## UGC stream validation engine

Sri Lankan university admissions require applicants to select three subjects at the G.C.E. Advanced Level examination in strict adherence to UGC subject group rules. The validation engine (`src/validator/engine.py`) implements these constraints algorithmically.

```
Biological Science Stream
  Requirement: Biology, Chemistry, and one from (Physics, Agricultural Science)

Physical Science Stream
  Requirement: Combined Mathematics, Physics, and one from (Chemistry, ICT, Applied Mathematics)

Engineering Technology Stream
  Requirement: Engineering Technology, Science for Technology, and one approved basket subject

Bio-systems Technology Stream
  Requirement: Bio-systems Technology, Science for Technology, and one approved basket subject

Commerce Stream
  Requirement: At least two primary commerce subjects (Accounting, Business Studies, Economics)
               plus one approved third subject

Arts Stream
  Requirement: Three subjects selected across four distinct linguistic, social, and aesthetic baskets
```

The engine implements hard constraint checks. For example, selecting Biology together with Combined Mathematics violates UGC circular requirements; the engine catches this pair and marks the combination invalid. Similarly, students in Technology streams cannot pick disallowed subjects for their third basket choice.

By evaluating the Cartesian combination of all registered A/L subjects against these rules, the engine dynamically constructs exactly 168 valid combinations. For student users entering an invalid curriculum, the validator computes minimum edit-distance single-subject swaps to indicate which change creates a compliant profile.

## Machine learning pipeline and artifact compression

### Model training formulation

The regression objective is to predict the cutoff Z-score for an undergraduate course $c$, university $u$, and district $d$ in exam year $t$:

$$\hat{y}_{c, u, d, t} = f(\text{CourseEnc}_c, \text{UniEnc}_u, \text{DistEnc}_d, \text{ExamYear}_t)$$

Categorical features are mapped using an `OrdinalEncoder` fitted only on historical records. To prevent temporal data leakage, validation splits are time-based: records prior to the latest recorded exam year form the training set, while the latest academic year serves as the out-of-time evaluation holdout.

The primary estimator is a `RandomForestRegressor` with 100 estimators. On the holdout evaluation set, the model achieves:

- Coefficient of Determination ($R^2$): 0.8364
- Mean Absolute Error (MAE): 0.089 Z-score units
- Root Mean Squared Error (RMSE): 0.124 Z-score units

### Artifact compression and runtime latency

Uncompressed serialization of a 100-tree ensemble produces a file size of 284.82 MB. Storing a 285 MB binary in git causes remote push timeouts on standard broadband networks and triggers GitHub file-size limits.

The training pipeline integrates lossless zlib compression (`joblib.dump(model, path, compress=6)`):

| Attribute | Uncompressed Model | Compressed Model (Level 6) |
|---|---|---|
| Serialized file size | 284.82 MB | 55.77 MB |
| Size reduction | Baseline | 80.4% reduction |
| Git push duration (330 KB/s upload) | > 14 minutes (failed) | 2 seconds |
| Startup decompression time | 1.1 seconds | 1.9 seconds |
| Warm inference latency | 28 ms | 30 ms |
| Decimal prediction consistency | Exact match | Exact match (down to $10^{-16}$) |

Decompression occurs once during the FastAPI service startup lifecycle. In-memory prediction requests execute against native NumPy arrays without repetitive decompression overhead.

## Application programming interface (API)

The production backend (`src/api/main.py`) is built with FastAPI. It handles prediction requests, candidate profile evaluations, and subject validations.

### Endpoint specifications

```
GET /health
Returns operational status, model availability, and database connectivity.

GET /metadata/options
Returns lists of standardized courses, universities, districts, and valid A/L subjects.

POST /predict
Calculates the expected cutoff Z-score for a single course, university, and district.
Returns the predicted mark, historical minimum, maximum, mean, and a competitiveness band.

POST /predict/batch
Accepts a list of course-university-district queries and calculates bulk predictions.

POST /evaluate/student
Compares a student's actual or projected Z-score against all programs in their district.
Categorizes programs into admission likelihood bands: Safe, Possible, Competitive, or Unlikely.

POST /validate/combination
Validates three selected subjects against UGC regulations and returns eligible streams.
```

### Rate limiting and security

To protect the server from automated scraping and denial-of-service spikes, the API incorporates IP-based rate limiting using `slowapi`:

- Default endpoints: 100 requests per minute
- Single prediction (`/predict`): 30 requests per minute
- Student evaluation (`/evaluate/student`): 20 requests per minute
- Batch inference (`/predict/batch`): 10 requests per minute

When limits are exceeded, the server returns HTTP 429 with standard `Retry-After` headers.

Cross-Origin Resource Sharing (CORS) middleware is configured to accept requests from configured domain origins, with wildcard support for local development.

## Web application interface

The user-facing frontend is a Single Page Application built with React 18, Vite, and Tailwind CSS. The interface is organized into three primary workspaces:

1. **Cutoff forecaster**: Allows students to select target universities and degree programs to view historical cutoffs and model forecasts alongside benchmark statistics.
2. **Student chance analyzer**: Accepts a student's home district and achieved Z-score, compares their score against all university options in the district, and displays admission feasibility rankings.
3. **University comparator**: Visualizes multi-campus cutoff differences for identical degree programs using Chart.js bar and line plots.

The frontend is compiled into static production bundles (`index.html`, CSS, and JS) located at `src/web/`. FastAPI mounts this directory at `/app/`, allowing the backend to serve both the API and the user interface from a single container instance without requiring a separate web proxy.

## Containerization and deployment

### Dockerfile construction

The deployment artifact uses a multi-stage `Dockerfile` to produce a minimal production image:

```dockerfile
# Stage 1: Build static frontend assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python runtime
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt
RUN useradd -m -u 1000 appuser
COPY src/ /app/src/
COPY models/ /app/models/
COPY data/bronze/db/al_cutoffs.db /app/data/bronze/db/al_cutoffs.db
COPY --from=frontend-builder /app/src/web /app/src/web
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Node.js build tools and `node_modules` are excluded from the runtime container. Python dependencies are installed using `uv` into system site-packages, and the application executes under an unprivileged `appuser` account. Dynamic port binding via `${PORT:-8000}` ensures compatibility with cloud runtimes that inject runtime port numbers.

### Continuous integration and image distribution

The GitHub Actions workflow (`.github/workflows/docker-publish.yml`) triggers on every push to the `main` branch:

1. Executes unit tests (`pytest tests/`) covering API endpoints, rate limiting, and subject validation.
2. Initializes Docker Buildx with GitHub Actions cache backends (`type=gha`).
3. Authenticates against Docker Hub using repository secrets (`DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`).
4. Builds and pushes the production container to Docker Hub under the tag `dilhara0592/image-test:latest`.

### Cloud deployment runbook

The platform can be deployed directly from the published Docker Hub image across multiple cloud hosting services:

#### Render.com
Use the repository blueprint [`render.yaml`](file:///D:/DS-Projects/al-trends/render.yaml):
1. Navigate to the Render dashboard and create a new Blueprint instance.
2. Select the `al-trends` repository.
3. Render reads `render.yaml`, builds the container, binds to `$PORT`, and initiates monitoring against `/health`.

#### Google Cloud Run
Deploy the pre-built container directly from Docker Hub:
```bash
gcloud run deploy al-trends \
    --image docker.io/dilhara0592/image-test:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1
```

#### Local execution via PowerShell
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& d:\DS-Projects\al-trends\.venv\Scripts\Activate.ps1)

# Run test suite
.\deploy.ps1 test

# Build and run container locally
.\deploy.ps1 docker-build
.\deploy.ps1 docker-run
```

## Verification and test coverage

The system contains an automated test suite in `tests/`:

- `test_api.py`: Validates root redirects, `/health` response payloads, metadata catalogue consistency, single-prediction responses, case-insensitive parameter handling, batch prediction arrays, student chance calculations, and rate-limiting enforcement.
- `test_validator.py`: Tests valid Biological Science selections, Technology stream basket validations, detection of disallowed pairs, and single-subject repair recommendations.

All 15 automated test cases run and pass prior to build packaging.
