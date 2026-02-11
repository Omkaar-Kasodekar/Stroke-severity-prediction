from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db import Base, DATABASE_URL, Prediction
from app.main import app


client = TestClient(app)


def _get_engine():
    return create_engine(DATABASE_URL, future=True)


def _reset_db() -> None:
    """Truncate predictions table between tests to get deterministic results."""
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE predictions RESTART IDENTITY;"))


def setup_function() -> None:
    # Called before each test function
    engine = _get_engine()
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    _reset_db()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_predict_basic_persistence():
    payload = {
        "age": 70,
        "bmi": 33.2,
        "avg_glucose_level": 165,
        "hypertension": 1,
        "heart_disease": 1,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert "severity" in data
    assert "model" in data

    prediction_id = data["prediction_id"]

    # Check it can be fetched via /predictions/{id}
    resp_get = client.get(f"/predictions/{prediction_id}")
    assert resp_get.status_code == 200
    obj = resp_get.json()
    assert obj["id"] == prediction_id
    assert obj["age"] == payload["age"]
    assert obj["bmi"] == payload["bmi"]
    assert obj["avg_glucose_level"] == payload["avg_glucose_level"]
    assert obj["hypertension"] == payload["hypertension"]
    assert obj["heart_disease"] == payload["heart_disease"]


def test_predict_extreme_values():
    # Very young, very low risk factors -> should be at least accepted by API
    low_risk = {
        "age": 18,
        "bmi": 18.5,
        "avg_glucose_level": 80,
        "hypertension": 0,
        "heart_disease": 0,
    }
    resp_low = client.post("/predict", json=low_risk)
    assert resp_low.status_code == 200
    data_low = resp_low.json()
    assert data_low["severity"] in ["mild", "moderate", "severe"]

    # Very high risk factors
    high_risk = {
        "age": 95,
        "bmi": 40.0,
        "avg_glucose_level": 300,
        "hypertension": 1,
        "heart_disease": 1,
    }
    resp_high = client.post("/predict", json=high_risk)
    assert resp_high.status_code == 200
    data_high = resp_high.json()
    assert data_high["severity"] in ["mild", "moderate", "severe"]


def test_predict_validation_errors():
    # Missing required field
    bad_payload_missing = {
        "age": 70,
        "bmi": 33.2,
        "avg_glucose_level": 165,
        "hypertension": 1,
        # "heart_disease" missing
    }
    resp_missing = client.post("/predict", json=bad_payload_missing)
    assert resp_missing.status_code == 422

    # Invalid type for a field
    bad_payload_type = {
        "age": "seventy",
        "bmi": 33.2,
        "avg_glucose_level": 165,
        "hypertension": 1,
        "heart_disease": 1,
    }
    resp_type = client.post("/predict", json=bad_payload_type)
    assert resp_type.status_code == 422

    # Out-of-range value for hypertension
    bad_payload_range = {
        "age": 70,
        "bmi": 33.2,
        "avg_glucose_level": 165,
        "hypertension": 2,  # must be 0 or 1
        "heart_disease": 1,
    }
    resp_range = client.post("/predict", json=bad_payload_range)
    assert resp_range.status_code == 422


def test_predictions_list_pagination():
    # Create multiple predictions
    for i in range(5):
        payload = {
            "age": 60 + i,
            "bmi": 25.0 + i,
            "avg_glucose_level": 120 + i,
            "hypertension": i % 2,
            "heart_disease": (i + 1) % 2,
        }
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 200

    # Default list (limit=50) should see all 5
    resp_list = client.get("/predictions")
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    assert data_list["total"] == 5
    assert len(data_list["items"]) == 5

    # Pagination: limit 2
    resp_page = client.get("/predictions?limit=2&offset=0")
    assert resp_page.status_code == 200
    data_page = resp_page.json()
    assert len(data_page["items"]) == 2


def test_get_prediction_not_found():
    resp = client.get("/predictions/999999")
    assert resp.status_code == 404
    data = resp.json()
    assert data["detail"] == "Prediction not found"

