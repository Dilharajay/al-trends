# ==============================================================================
# Multi-Stage Dockerfile for Sri Lanka A/L Cutoff AI
# Stage 1: Build React/Vite Frontend
# Stage 2: Production Python API Runtime
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Builder
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package manifests first for efficient layer caching
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --prefer-offline --no-audit || npm install

# Copy frontend source code and configs
COPY frontend/ ./

# Build static assets (Vite outputs to /app/src/web)
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Set environment variables for Python and application runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    APP_ENV=production

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv binary from official Astral image for ultra-fast, reliable dependency installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install Python requirements
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Create non-root application user for container security
RUN useradd -m -u 1000 appuser

# Copy application source code and models
COPY src/ /app/src/
COPY models/ /app/models/
COPY data/bronze/db/al_cutoffs.db /app/data/bronze/db/al_cutoffs.db

# Copy compiled frontend from Stage 1 into /app/src/web
COPY --from=frontend-builder /app/src/web /app/src/web

# Set correct ownership for non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose HTTP port (overridable via PORT env var in cloud platforms)
EXPOSE 8000

# Container healthcheck querying FastAPI /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch production server with dynamic port support (Render, Railway, Cloud Run, etc.)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
