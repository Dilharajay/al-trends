import os
import pickle
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import joblib

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder

from src.validator.engine import validateCombination, ALL_SUBJECTS
from src.api.schemas import (
    PredictionRequest,
    PredictionResponse,
    HistoricalStats,
    BatchPredictionResponse,
    StudentEvaluationResponse,
    StudentEvaluationItem,
    CombinationValidationResponse,
    MetadataResponse,
    HealthResponse,
)


class MLModelService:
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        
        self.model_path = project_root / "models" / "rf_model.pkl"
        self.encoder_path = project_root / "models" / "encoders.pkl"
        self.db_path = project_root / "data" / "bronze" / "db" / "al_cutoffs.db"
        
        self.model: Optional[RandomForestRegressor] = None
        self.encoder: Optional[OrdinalEncoder] = None
        
        self.course_map: Dict[str, str] = {}
        self.uni_map: Dict[str, str] = {}
        self.district_map: Dict[str, str] = {}
        
        self.historical_stats_cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self.course_uni_pairs: List[Tuple[str, str]] = []
        self.uni_to_courses: Dict[str, List[str]] = {}
        self.course_to_unis: Dict[str, List[str]] = {}
        
        self.load_artifacts()
        self.load_database_metadata()

    def load_artifacts(self) -> None:
        """Load serialized Random Forest model and OrdinalEncoder."""
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
        else:
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

        if self.encoder_path.exists():
            with open(self.encoder_path, "rb") as f:
                self.encoder = pickle.load(f)
                
            # Build case-insensitive lookup dictionaries
            raw_courses = list(self.encoder.categories_[0])
            raw_unis = list(self.encoder.categories_[1])
            raw_districts = list(self.encoder.categories_[2])
            
            self.course_map = {c.strip().upper(): c for c in raw_courses}
            self.uni_map = {u.strip().lower(): u for u in raw_unis}
            self.district_map = {d.strip().upper(): d for d in raw_districts}
        else:
            raise FileNotFoundError(f"Encoder file not found at {self.encoder_path}")

    def load_database_metadata(self) -> None:
        """Preload historical cutoff statistics for fast constant-time lookup."""
        if not self.db_path.exists():
            return

        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            c.CourseName,
            u.UniversityName,
            d.DistrictName,
            f.CutoffZ
        FROM fact_cutoffs f
        JOIN dim_course c ON f.CourseID = c.CourseID
        JOIN dim_university u ON f.UniversityID = u.UniversityID
        JOIN dim_district d ON f.DistrictID = d.DistrictID
        WHERE f.CutoffZ IS NOT NULL
        """
        try:
            df = pd.read_sql(query, conn)
            # Group by and aggregate
            grouped = df.groupby(["CourseName", "UniversityName", "DistrictName"])["CutoffZ"]
            for (c, u, d), series in grouped:
                self.historical_stats_cache[(c, u, d)] = {
                    "mean": float(series.mean()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "std": float(series.std()) if len(series) > 1 else 0.0,
                    "count": int(len(series))
                }
            self.course_uni_pairs = df[["CourseName", "UniversityName"]].drop_duplicates().values.tolist()
            
            self.uni_to_courses = {}
            self.course_to_unis = {}
            for c_name, u_name in self.course_uni_pairs:
                self.uni_to_courses.setdefault(u_name, []).append(c_name)
                self.course_to_unis.setdefault(c_name, []).append(u_name)
            for u in self.uni_to_courses:
                self.uni_to_courses[u].sort()
            for c in self.course_to_unis:
                self.course_to_unis[c].sort()
        finally:
            conn.close()

    def resolve_identifiers(self, course: str, uni: str, district: str) -> Tuple[str, str, str]:
        """Normalize inputs and resolve to canonical names."""
        c_clean = course.strip().upper()
        u_clean = uni.strip().lower()
        d_clean = district.strip().upper()

        c_canonical = self.course_map.get(c_clean, course.strip())
        u_canonical = self.uni_map.get(u_clean, uni.strip())
        d_canonical = self.district_map.get(d_clean, district.strip())

        return c_canonical, u_canonical, d_canonical

    def _determine_competitiveness_band(self, z_score: float) -> str:
        """Categorize cutoff difficulty based on predicted Z-score."""
        if z_score >= 2.0:
            return "Extremely Competitive"
        elif z_score >= 1.6:
            return "Highly Competitive"
        elif z_score >= 1.2:
            return "Competitive"
        elif z_score >= 0.8:
            return "Moderate"
        else:
            return "Lower Historical Cutoff"

    def predict_single(self, req: PredictionRequest) -> PredictionResponse:
        c_name, u_name, d_name = self.resolve_identifiers(req.course_name, req.university_name, req.district_name)
        
        # Ordinal encode with feature names
        input_df = pd.DataFrame([[c_name, u_name, d_name]], columns=["CourseName", "UniversityName", "DistrictName"])
        encoded = self.encoder.transform(input_df)
        features = pd.DataFrame([{
            "ExamYear": req.exam_year,
            "Course_Enc": encoded[0][0],
            "Uni_Enc": encoded[0][1],
            "Dist_Enc": encoded[0][2]
        }])
        
        pred_z = float(self.model.predict(features)[0])
        pred_z = round(pred_z, 4)
        
        # Historical stats lookup
        hist_data = self.historical_stats_cache.get((c_name, u_name, d_name))
        stats_obj = None
        if hist_data:
            stats_obj = HistoricalStats(
                mean=round(hist_data["mean"], 4),
                min=round(hist_data["min"], 4),
                max=round(hist_data["max"], 4),
                std=round(hist_data["std"], 4),
                sample_count=hist_data["count"]
            )
            
        band = self._determine_competitiveness_band(pred_z)
        
        return PredictionResponse(
            course_name=c_name,
            university_name=u_name,
            district_name=d_name,
            exam_year=req.exam_year,
            predicted_cutoff_z=pred_z,
            historical_stats=stats_obj,
            competitiveness_band=band
        )

    def predict_batch(self, items: List[PredictionRequest]) -> BatchPredictionResponse:
        predictions = [self.predict_single(req) for req in items]
        return BatchPredictionResponse(
            total_processed=len(predictions),
            predictions=predictions
        )

    def evaluate_student(
        self,
        student_z: float,
        district: str,
        course_filter: Optional[str] = None,
        exam_year: int = 2026
    ) -> StudentEvaluationResponse:
        """Evaluate a student's eligibility across all universities offering matching courses."""
        _, _, d_canonical = self.resolve_identifiers("", "", district)
        
        # Filter course-university offerings
        pairs = self.course_uni_pairs
        if course_filter:
            c_filter_clean = course_filter.strip().upper()
            pairs = [p for p in pairs if c_filter_clean in p[0].upper()]

        evaluations: List[StudentEvaluationItem] = []
        eligible_count = 0
        
        for c_name, u_name in pairs:
            req = PredictionRequest(
                course_name=c_name,
                university_name=u_name,
                district_name=d_canonical,
                exam_year=exam_year
            )
            res = self.predict_single(req)
            pred_z = res.predicted_cutoff_z
            margin = round(student_z - pred_z, 4)
            
            # Eligibility categorization:
            # Safe: margin >= +0.08
            # Possible: 0.0 <= margin < +0.08
            # Competitive: -0.08 <= margin < 0.0
            # Unlikely: margin < -0.08
            if margin >= 0.08:
                status = "Safe"
                eligible_count += 1
            elif margin >= 0.0:
                status = "Possible"
                eligible_count += 1
            elif margin >= -0.08:
                status = "Competitive"
            else:
                status = "Unlikely"
                
            evaluations.append(StudentEvaluationItem(
                course_name=c_name,
                university_name=u_name,
                predicted_cutoff_z=pred_z,
                margin=margin,
                status=status
            ))

        # Sort by margin descending (safest options first)
        evaluations.sort(key=lambda x: x.margin, reverse=True)

        return StudentEvaluationResponse(
            student_z_score=student_z,
            district_name=d_canonical,
            exam_year=exam_year,
            total_evaluated=len(evaluations),
            eligible_count=eligible_count,
            evaluations=evaluations
        )

    def validate_ugc_combination(self, subjects: List[str]) -> CombinationValidationResponse:
        streams, reason, swaps = validateCombination(subjects, with_swaps=True)
        is_valid = len(streams) > 0
        return CombinationValidationResponse(
            is_valid=is_valid,
            matching_streams=streams,
            failure_reason=reason,
            suggested_swaps=swaps
        )

    def get_metadata(self) -> MetadataResponse:
        courses = sorted(list(self.course_map.values()))
        unis = sorted(list(self.uni_map.values()))
        districts = sorted(list(self.district_map.values()))
        subjects = sorted(list(ALL_SUBJECTS))
        return MetadataResponse(
            total_courses=len(courses),
            total_universities=len(unis),
            total_districts=len(districts),
            total_subjects=len(subjects),
            courses=courses,
            universities=unis,
            districts=districts,
            subjects=subjects,
            university_courses=self.uni_to_courses,
            course_universities=self.course_to_unis
        )

    def get_health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            model_loaded=self.model is not None,
            encoder_loaded=self.encoder is not None,
            database_connected=self.db_path.exists(),
            supported_courses=len(self.course_map),
            supported_universities=len(self.uni_map),
            supported_districts=len(self.district_map)
        )
