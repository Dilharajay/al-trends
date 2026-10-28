# Web Frontend & REST API Architecture Guide

This document outlines the architecture, specifications, rate-limiting policies, and deployment strategies for the **Sri Lanka A/L Cutoffs ML API** and its **Web Frontend**.

---

## 1. System Overview

The system delivers an end-to-end serving layer for the trained `RandomForestRegressor` and UGC combinatorial rule engine:

```
┌────────────────────────────────────────────────────────┐
│                   Client Layer                         │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │   Web SPA (HTML/JS)   │   │ External API Clients │  │
│  │ (Tailwind / Chart.js) │   │ (cURL / Python / App)│  │
│  └───────────┬───────────┘   └───────────┬──────────┘  │
└──────────────┼───────────────────────────┼─────────────┘
               │                           │
               ▼                           ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Serving Layer                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │     SlowAPI Rate Limiter (IP Sliding Window)     │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             ▼                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │                Route Handlers                    │  │
│  │  /predict  /evaluate/student  /validate/...      │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             ▼                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │                 ML Model Service                 │  │
│  │   - Preloaded Random Forest (rf_model.pkl)       │  │
│  │   - OrdinalEncoder (encoders.pkl)                │  │
│  │   - Cached Star Schema Aggregates (SQLite)       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Web Frontend (Zero-Build Deployable SPA)

The web frontend (`src/web/`) is built **without Streamlit**, eliminating heavy server-side Python socket overhead. It is a lightweight, responsive Single Page Application (SPA) utilizing:
- **Tailwind CSS (CDN)**: Modern responsive design system.
- **Lucide Icons (CDN)**: Clean, semantic vector iconography.
- **Chart.js (CDN)**: Client-side interactive canvas charts.
- **Vanilla Modern JS**: Fetch API, local storage configuration, zero-build deployment.

### Features & User Workflows:
1. **Live System Telemetry & Rate-Limit Tracking**:
   - Live health indicator polling `/health` with pulse animation.
   - Dynamic quota tracking (`x-ratelimit-remaining` / `x-ratelimit-limit`) updated on every request.
   - Settings modal allowing users to point the frontend to any remote or local API base URL.
2. **🔮 Cutoff Z-Score Forecaster**:
   - Dropdown selection from 131 UGC courses, 21 universities, and 25 administrative districts.
   - Outputs predicted cutoff Z-score, competitiveness tier, and comparison against historical averages.
   - Visual Z-score scale benchmark pin.
3. **🎓 Student Admission Analyzer**:
   - Evaluates a student's actual or projected Z-score against all universities offering target degrees in their district.
   - Computes admission margins ($\Delta Z = Z_{\text{student}} - Z_{\text{forecast}}$).
   - Renders a horizontal bar chart and table color-coded into **Safe** (🟢), **Possible** (🔵), **Competitive** (🟠), and **Unlikely** (🔴).
4. **⚖️ UGC Subject Combination Rule Engine**:
   - Interactive 3-subject selector with one-click presets (Biological Science, Physical Science, Engineering Tech, Disallowed Pair).
   - Enforces official circular rules, explains violation causes, and recommends single-subject swaps.
5. **📊 Multi-University Batch Forecaster**:
   - Benchmarks cutoffs across all state universities in a single API round-trip (`POST /predict/batch`).

---

## 3. REST API Specification

### Base Endpoints

#### `GET /`
- **Description**: Root entrypoint. If requested via a web browser (`Accept: text/html`), it redirects to the web frontend at `/app/`. When requested by API clients, returns system metadata JSON.
- **Rate Limit**: 60 requests/minute.

#### `GET /health`
- **Description**: Returns operational health, model loading status, version, and catalogue counts.
- **Rate Limit**: 60 requests/minute.
- **Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "encoder_loaded": true,
  "database_connected": true,
  "supported_courses": 131,
  "supported_universities": 21,
  "supported_districts": 25
}
```

#### `GET /metadata/options`
- **Description**: Returns full standardized catalogues for autocomplete and dropdown selectors.
- **Rate Limit**: 30 requests/minute.

---

### Prediction & Evaluation Endpoints

#### `POST /predict`
- **Description**: Forecasts cutoff Z-score for a single course-university-district combination.
- **Rate Limit**: 30 requests/minute.
- **Request**:
```json
{
  "course_name": "MEDICINE",
  "university_name": "University of Colombo",
  "district_name": "COLOMBO",
  "exam_year": 2026
}
```
- **Response**:
```json
{
  "course_name": "MEDICINE",
  "university_name": "University of Colombo",
  "district_name": "COLOMBO",
  "exam_year": 2026,
  "predicted_cutoff_z": 2.36,
  "historical_stats": {
    "mean": 2.3531,
    "min": 2.215,
    "max": 2.459,
    "std": 0.0824,
    "sample_count": 8
  },
  "competitiveness_band": "Extremely Competitive"
}
```

#### `POST /predict/batch`
- **Description**: Forecasts cutoffs for a list of combinations in a single batch request.
- **Rate Limit**: 10 requests/minute.

#### `POST /evaluate/student`
- **Description**: Evaluates student admission probability and margins across degree programs.
- **Rate Limit**: 20 requests/minute.
- **Request**:
```json
{
  "student_z_score": 1.85,
  "district_name": "COLOMBO",
  "course_name": "ENGINEERING",
  "exam_year": 2026
}
```

#### `POST /validate/combination`
- **Description**: Validates 3 subjects against UGC admission circulars.
- **Rate Limit**: 60 requests/minute.
- **Request**:
```json
{
  "subjects": ["Biology", "Combined Mathematics", "Chemistry"]
}
```
- **Response**:
```json
{
  "is_valid": false,
  "matching_streams": [],
  "failure_reason": "disallowed pair: Biology and Combined Mathematics cannot sit in the same combination per the UGC stream-definition circular",
  "suggested_swaps": [
    "replace Combined Mathematics with Physics to qualify for Biological Science",
    "replace Biology with Physics to qualify for Physical Science"
  ]
}
```

---

## 4. Rate Limiting Policy

The API uses **`slowapi`** with sliding-window algorithms based on the client's remote IP address (`get_remote_address`).

### Headers Returned on Every Request
- `X-RateLimit-Limit`: Maximum requests permitted per window.
- `X-RateLimit-Remaining`: Remaining request count in the current window.
- `X-RateLimit-Reset`: Unix epoch timestamp when quota resets.

### HTTP 429 Error Format
```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests: 10 per 1 minute. Please slow down.",
  "status_code": 429
}
```

---

## 5. Deployment Options

### Option A: Unified FastAPI Serving (Recommended)
FastAPI serves **both** the REST API and the static web frontend from a single port without additional servers:

```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
- Web Application: `http://localhost:8000/app/` (or `http://localhost:8000/`)
- API Docs: `http://localhost:8000/docs`

### Option B: Decoupled Static Hosting (Vercel / Netlify / GitHub Pages)
Because `src/web/` consists purely of static HTML, CSS, and JavaScript:
1. Deploy the `src/web/` directory to any static hosting provider (e.g. GitHub Pages, Vercel, Netlify, AWS S3 / CloudFront).
2. Deploy the FastAPI backend on any container service (e.g. AWS ECS, GCP Cloud Run, Render, Railway).
3. The frontend includes a built-in Settings modal where users can configure the API endpoint URL, storing it in `localStorage`.

### Option C: Production Containerization (Docker)
A production `Dockerfile` can package both the model artifacts and the serving layer:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY data/bronze/ data/bronze/
COPY models/ models/
COPY src/ src/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
