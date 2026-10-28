import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_web_frontend_mounted(client):
    # Test browser redirect on root
    browser_resp = client.get("/", headers={"accept": "text/html,application/xhtml+xml"}, follow_redirects=False)
    assert browser_resp.status_code in [302, 307]
    assert browser_resp.headers["location"] == "/app/"

    # Test static files serving HTML
    app_resp = client.get("/app/")
    assert app_resp.status_code == 200
    assert "Sri Lanka A/L" in app_resp.text
    assert '<div id="root"></div>' in app_resp.text



def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["encoder_loaded"] is True
    assert data["supported_courses"] > 50
    assert data["supported_districts"] == 25


def test_metadata_endpoint(client):
    response = client.get("/metadata/options")
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert "universities" in data
    assert "districts" in data
    assert "subjects" in data
    assert "university_courses" in data
    assert "course_universities" in data
    assert "MEDICINE" in data["courses"]
    assert "COLOMBO" in data["districts"]
    assert "Combined Mathematics" in data["subjects"]

    # Verify offerings mapping
    assert "University of Colombo" in data["university_courses"]
    assert "MEDICINE" in data["university_courses"]["University of Colombo"]
    # Visual & Performing Arts does not offer Medicine
    assert "MEDICINE" not in data["university_courses"].get("University of the Visual & Performing Arts", [])
    # Engineering is offered by Moratuwa
    assert "University of Moratuwa" in data["course_universities"].get("ENGINEERING", [])


def test_predict_single_endpoint(client):
    payload = {
        "course_name": "MEDICINE",
        "university_name": "University of Colombo",
        "district_name": "COLOMBO",
        "exam_year": 2026
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "MEDICINE"
    assert data["university_name"] == "University of Colombo"
    assert data["district_name"] == "COLOMBO"
    assert data["exam_year"] == 2026
    assert isinstance(data["predicted_cutoff_z"], float)
    assert data["predicted_cutoff_z"] > 1.5
    assert data["historical_stats"] is not None
    assert data["historical_stats"]["sample_count"] > 0
    assert data["competitiveness_band"] in ["Extremely Competitive", "Highly Competitive", "Competitive"]


def test_predict_case_insensitivity(client):
    # Lowercase inputs should be resolved seamlessly
    payload = {
        "course_name": "medicine",
        "university_name": "university of colombo",
        "district_name": "colombo",
        "exam_year": 2026
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "MEDICINE"
    assert data["university_name"] == "University of Colombo"
    assert data["district_name"] == "COLOMBO"


def test_predict_batch_endpoint(client):
    payload = {
        "items": [
            {
                "course_name": "ENGINEERING",
                "university_name": "University of Moratuwa",
                "district_name": "KANDY",
                "exam_year": 2026
            },
            {
                "course_name": "COMPUTER SCIENCE",
                "university_name": "University of Colombo School of Computing",
                "district_name": "GALLE",
                "exam_year": 2026
            }
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["course_name"] == "ENGINEERING"


def test_evaluate_student_endpoint(client):
    payload = {
        "student_z_score": 2.1,
        "district_name": "COLOMBO",
        "course_name": "ENGINEERING",
        "exam_year": 2026
    }
    response = client.post("/evaluate/student", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["student_z_score"] == 2.1
    assert data["district_name"] == "COLOMBO"
    assert data["total_evaluated"] > 0
    assert len(data["evaluations"]) > 0
    first = data["evaluations"][0]
    assert "status" in first
    assert first["status"] in ["Safe", "Possible", "Competitive", "Unlikely"]


def test_validate_combination_endpoint(client):
    # Valid Physical Science combination
    valid_payload = {
        "subjects": ["Combined Mathematics", "Physics", "Chemistry"]
    }
    response = client.post("/validate/combination", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "Physical Science" in data["matching_streams"]

    # Invalid Disallowed Pair (Bio + Combined Maths)
    invalid_payload = {
        "subjects": ["Combined Mathematics", "Biology", "Chemistry"]
    }
    response = client.post("/validate/combination", json=invalid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "disallowed pair" in data["failure_reason"]
    assert len(data["suggested_swaps"]) > 0


def test_rate_limit_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    # slowapi injects rate limit headers when headers_enabled=True
    assert "x-ratelimit-limit" in response.headers or "retry-after" in response.headers or "x-ratelimit-remaining" in response.headers


def test_rate_limiting_triggered(client):
    payload = {
        "items": [
            {
                "course_name": "MEDICINE",
                "university_name": "University of Colombo",
                "district_name": "COLOMBO",
                "exam_year": 2026
            }
        ]
    }
    # /predict/batch has a limit of 10/minute
    statuses = []
    for _ in range(12):
        res = client.post("/predict/batch", json=payload)
        statuses.append(res.status_code)

    assert 429 in statuses
    last_res = client.post("/predict/batch", json=payload)
    assert last_res.status_code == 429
    data = last_res.json()
    assert data["error"] == "Rate limit exceeded"
    assert "Too many requests" in data["detail"]
    assert data["status_code"] == 429

