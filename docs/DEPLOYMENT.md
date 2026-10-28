# Docker Hub & Cloud Deployment Guide

This document details how **AL Trends (Sri Lanka A/L Cutoff AI)** is containerized with Docker, published to **Docker Hub (`dilhara0592/image-test`)**, and deployed to cloud hosting platforms.

---

## 1. Container Architecture

The application uses an optimized **multi-stage Docker build** defined in [`Dockerfile`](file:///D:/DS-Projects/al-trends/Dockerfile):

```
┌───────────────────────────────────────────────┐
│ Stage 1: Frontend Builder (node:20-alpine)    │
│  - Installs npm dependencies                  │
│  - Compiles React + Vite + Tailwind           │
│  - Generates static bundles in /app/src/web   │
└───────────────────────┬───────────────────────┘
                        │
                        ▼ (Static bundles copied)
┌───────────────────────────────────────────────┐
│ Stage 2: Runtime (python:3.11-slim)           │
│  - Installs system packages (curl)            │
│  - High-speed uv pip install requirements     │
│  - Copies models (compressed 55MB), DB, & src │
│  - Creates unprivileged appuser (security)    │
│  - Dynamically binds to $PORT (FastAPI/Uvicorn│
│  - Container HEALTHCHECK on /health           │
└───────────────────────────────────────────────┘
```

### Key Highlights:
- **Compressed Model Artifacts**: Model file (`models/rf_model.pkl`) is compressed via `joblib` from 285 MB down to **55.7 MB** (80% size reduction), speeding up downloads and container startup.
- **Zero-Node Runtime**: Node.js and `node_modules` are discarded after Stage 1, reducing the final image size and attack surface.
- **Dynamic Port Support**: The container reads `$PORT` (injected by cloud services like Render, Cloud Run, and Railway) with a fallback to `8000`.
- **Built-in Health Checks**: Docker monitors `GET /health` every 30 seconds to report container health to orchestrators.

---

## 2. Docker Hub Integration

### Target Image Repository
```text
dilhara0592/image-test:latest
```

### Automated CI/CD Pipeline (GitHub Actions)
The repository includes a GitHub Actions workflow at [`.github/workflows/docker-publish.yml`](file:///D:/DS-Projects/al-trends/.github/workflows/docker-publish.yml).

Every `git push` to `main` will:
1. Run the test suite (`pytest tests/`) to ensure code quality.
2. Build the multi-stage Docker image with Docker Buildx.
3. Authenticate to Docker Hub using GitHub Repository Secrets.
4. Push `dilhara0592/image-test:latest` and SHA tags directly to Docker Hub.

### Adding Docker Hub Credentials to GitHub:
To allow the automated GitHub Action to push to Docker Hub:
1. Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add:
   - `DOCKERHUB_USERNAME`: your Docker Hub username (`dilhara0592`)
   - `DOCKERHUB_TOKEN`: your Docker Hub Personal Access Token (generate at [hub.docker.com/settings/security](https://hub.docker.com/settings/security))

---

## 3. Cloud Deployment Guides

### Option A: Render.com (Recommended - 1-Click Blueprint)

The repository provides a [`render.yaml`](file:///D:/DS-Projects/al-trends/render.yaml) blueprint specification.

1. Go to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository `https://github.com/Dilharajay/al-trends`.
4. Render will parse `render.yaml` automatically and configure:
   - Runtime: Docker
   - Health Check Path: `/health`
   - Port: Render automatically assigns `$PORT`
5. Click **Apply**. Your app and interactive frontend will be live in minutes.

---

### Option B: Railway.app

The repository includes [`railway.toml`](file:///D:/DS-Projects/al-trends/railway.toml).

1. Log into [railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select `Dilharajay/al-trends`.
4. Railway will automatically detect the `Dockerfile` and `railway.toml`.
5. Under service settings, generate a domain (e.g. `al-trends.up.railway.app`).

---

### Option C: Google Cloud Run (Serverless Container)

Deploy directly using the published Docker Hub image:

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

---

### Option D: AWS App Runner

1. Open the **AWS App Runner** console.
2. Click **Create service**.
3. Choose **Container registry** -> **Public registry**.
4. Enter container image URI: `docker.io/dilhara0592/image-test:latest`.
5. Under Port, enter `8000`.
6. Click **Deploy**.

---

## 4. Local Development & Docker Commands

You can use the PowerShell helper script [`deploy.ps1`](file:///D:/DS-Projects/al-trends/deploy.ps1) or native commands:

### Activating the Virtual Environment
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "d:\DS-Projects\al-trends\.venv\Scripts\Activate.ps1"
```

### Running Tests
```powershell
.\deploy.ps1 test
# OR: pytest tests/ -v
```

### Local Docker Build & Test (If Docker is installed)
```powershell
# Build image for Docker Hub locally
docker build -t dilhara0592/image-test:latest .

# Run container locally
docker run --rm -p 8000:8000 dilhara0592/image-test:latest

# Push directly to Docker Hub from CLI
docker push dilhara0592/image-test:latest

# Or run with docker-compose
docker compose up --build
```

### Verify Endpoints
Once running locally or in the cloud:
- **Web App**: `http://localhost:8000/app/` (or `http://localhost:8000/`)
- **Health Check**: `http://localhost:8000/health`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 5. Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `production` | Environment mode (`production`, `development`) |
| `APP_NAME` | `Sri Lanka A/L Cutoff AI` | API and application title |
| `PORT` / `API_PORT` | `8000` | Port the HTTP server binds to (assigned dynamically in cloud) |
| `API_HOST` | `0.0.0.0` | Host IP binding (must be `0.0.0.0` inside containers) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated list for custom domains) |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Default slowapi rate limit |
| `RATE_LIMIT_PREDICT` | `30/minute` | Single prediction rate limit |
| `RATE_LIMIT_BATCH` | `10/minute` | Batch prediction rate limit |
| `RATE_LIMIT_STUDENT` | `20/minute` | Student eligibility evaluation rate limit |
