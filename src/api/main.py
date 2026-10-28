import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse

# Load environment configuration from .env
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "production")
APP_NAME = os.getenv("APP_NAME", "Sri Lanka A/L Cutoff AI")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
API_RELOAD = os.getenv("API_RELOAD", "false").lower() in ("true", "1", "yes")

CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_RAW.split(",") if orig.strip()]

RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
RATE_LIMIT_PREDICT = os.getenv("RATE_LIMIT_PREDICT", "30/minute")
RATE_LIMIT_BATCH = os.getenv("RATE_LIMIT_BATCH", "10/minute")
RATE_LIMIT_STUDENT = os.getenv("RATE_LIMIT_STUDENT", "20/minute")

from src.api.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    StudentEvaluationRequest,
    StudentEvaluationResponse,
    CombinationValidationRequest,
    CombinationValidationResponse,
    MetadataResponse,
    HealthResponse,
)
from src.api.service import MLModelService

# Initialize slowapi rate limiter based on client remote IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
    headers_enabled=True,
)

# Global service instance
ml_service: Optional[MLModelService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_service
    # Initialize and cache model and database on startup
    ml_service = MLModelService()
    yield
    # Cleanup on shutdown if needed
    ml_service = None


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom 429 response formatter returning structured JSON."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests: {exc.detail}. Please slow down.",
            "status_code": 429,
        },
    )


app = FastAPI(
    title=APP_NAME,
    description="""
    Production-ready REST API for predicting Sri Lankan G.C.E. Advanced Level (A/L) university cutoff Z-scores,
    evaluating student admission eligibility, and serving a React Single Page Application.
    Rate-limited via slowapi to prevent denial-of-service and brute-force overuse.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Path to web frontend directory
web_dir = Path(__file__).resolve().parent.parent / "web"


@app.get("/", summary="Root Endpoint")
@limiter.limit("60/minute")
def read_root(request: Request, response: Response):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and web_dir.exists():
        return RedirectResponse(url="/app/")
    return {
        "message": f"Welcome to the {APP_NAME} API",
        "version": "1.0.0",
        "web_app": "/app/",
        "docs_url": "/docs",
        "health_check": "/health",
        "metadata_url": "/metadata/options",
        "rate_limiting": "Enabled (slowapi)"
    }


# Mount StaticFiles for the React frontend
if web_dir.exists():
    app.mount("/app", StaticFiles(directory=str(web_dir), html=True), name="web")


@app.get("/health", response_model=HealthResponse, summary="API Health Check")
@limiter.limit("60/minute")
def health_check(request: Request, response: Response):
    """Returns the operational status of the service, model artifacts, and database connection."""
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    return ml_service.get_health()


@app.get("/metadata/options", response_model=MetadataResponse, summary="Catalogue Metadata")
@limiter.limit("30/minute")
def get_metadata(request: Request, response: Response):
    """Returns all standardized courses, universities, districts, and valid A/L subjects."""
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    return ml_service.get_metadata()


@app.post("/predict", response_model=PredictionResponse, summary="Predict Single Cutoff Z-Score")
@limiter.limit(RATE_LIMIT_PREDICT)
def predict_cutoff(request: Request, response: Response, payload: PredictionRequest):
    """
    Forecast the minimum qualifying Z-Score cutoff for a specific course, university, and district.
    Includes historical benchmarks (mean, min, max, std) and competitiveness classification.
    """
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    try:
        return ml_service.predict_single(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse, summary="Batch Cutoff Predictions")
@limiter.limit(RATE_LIMIT_BATCH)
def predict_batch(request: Request, response: Response, payload: BatchPredictionRequest):
    """Efficiently forecasts cutoffs for a batch list of course-university-district combinations."""
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    try:
        return ml_service.predict_batch(payload.items)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/evaluate/student", response_model=StudentEvaluationResponse, summary="Evaluate Student Admission Chances")
@limiter.limit(RATE_LIMIT_STUDENT)
def evaluate_student(request: Request, response: Response, payload: StudentEvaluationRequest):
    """
    Analyzes a student's actual or projected Z-Score against all university programs in their district.
    Ranks options by admission margin and categorizes into Safe, Possible, Competitive, or Unlikely.
    """
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    try:
        return ml_service.evaluate_student(
            student_z=payload.student_z_score,
            district=payload.district_name,
            course_filter=payload.course_name,
            exam_year=payload.exam_year
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/validate/combination", response_model=CombinationValidationResponse, summary="Validate A/L Subject Combination")
@limiter.limit("60/minute")
def validate_combination(request: Request, response: Response, payload: CombinationValidationRequest):
    """
    Validates a 3-subject combination against official UGC circular rules.
    Detects disallowed pairs (e.g., Biology + Combined Maths) and barred technology subjects,
    returning eligible streams or single-subject swap recommendations.
    """
    if ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service not initialized.")
    try:
        return ml_service.validate_ugc_combination(payload.subjects)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD)
