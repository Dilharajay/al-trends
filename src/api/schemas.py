from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    course_name: str = Field(..., description="Course name (e.g., 'MEDICINE', 'ENGINEERING')", json_schema_extra={"example": "MEDICINE"})
    university_name: str = Field(..., description="University name", json_schema_extra={"example": "University of Colombo"})
    district_name: str = Field(..., description="District name", json_schema_extra={"example": "COLOMBO"})
    exam_year: int = Field(default=2026, description="A/L Examination year to forecast", json_schema_extra={"example": 2026})


class HistoricalStats(BaseModel):
    mean: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    std: Optional[float] = None
    sample_count: int = 0


class PredictionResponse(BaseModel):
    course_name: str
    university_name: str
    district_name: str
    exam_year: int
    predicted_cutoff_z: float
    historical_stats: Optional[HistoricalStats] = None
    competitiveness_band: Optional[str] = None


class BatchPredictionRequest(BaseModel):
    items: List[PredictionRequest] = Field(..., description="List of individual prediction requests")


class BatchPredictionResponse(BaseModel):
    total_processed: int
    predictions: List[PredictionResponse]


class StudentEvaluationRequest(BaseModel):
    student_z_score: float = Field(..., description="Student's actual or projected Z-Score", json_schema_extra={"example": 1.85})
    district_name: str = Field(..., description="Candidate's administrative district", json_schema_extra={"example": "COLOMBO"})
    course_name: Optional[str] = Field(default=None, description="Optional target course filter", json_schema_extra={"example": "ENGINEERING"})
    exam_year: int = Field(default=2026, description="Target forecast exam year", json_schema_extra={"example": 2026})


class StudentEvaluationItem(BaseModel):
    course_name: str
    university_name: str
    predicted_cutoff_z: float
    margin: float
    status: str = Field(..., description="Eligibility category: 'Safe', 'Possible', 'Competitive', or 'Unlikely'")


class StudentEvaluationResponse(BaseModel):
    student_z_score: float
    district_name: str
    exam_year: int
    total_evaluated: int
    eligible_count: int
    evaluations: List[StudentEvaluationItem]


class CombinationValidationRequest(BaseModel):
    subjects: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 distinct A/L subjects",
        json_schema_extra={"example": ["Combined Mathematics", "Physics", "Chemistry"]}
    )


class CombinationValidationResponse(BaseModel):
    is_valid: bool
    matching_streams: List[str]
    failure_reason: Optional[str] = None
    suggested_swaps: List[str] = []


class MetadataResponse(BaseModel):
    total_courses: int
    total_universities: int
    total_districts: int
    total_subjects: int
    courses: List[str]
    universities: List[str]
    districts: List[str]
    subjects: List[str]
    university_courses: Dict[str, List[str]] = Field(default_factory=dict, description="Mapping of each university to its offered courses")
    course_universities: Dict[str, List[str]] = Field(default_factory=dict, description="Mapping of each course to universities offering it")


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    encoder_loaded: bool
    database_connected: bool
    supported_courses: int
    supported_universities: int
    supported_districts: int
