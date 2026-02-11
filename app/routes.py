from pathlib import Path
from typing import Annotated, Optional

import joblib
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import schemas
from .db import Prediction, get_db


router = APIRouter()


MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
DT_MODEL_PATH = MODEL_DIR / "decision_tree.joblib"
GB_MODEL_PATH = MODEL_DIR / "gradient_boosting.joblib"


def _load_model(path: Path) -> Optional[object]:
    if path.exists():
        return joblib.load(path)
    return None


decision_tree_model = _load_model(DT_MODEL_PATH)
gradient_boosting_model = _load_model(GB_MODEL_PATH)


class SimpleFallbackModel:
    """Very simple rule-based model used if joblib models are missing."""

    classes_ = np.array(["mild", "moderate", "severe"])

    def predict(self, X: np.ndarray):
        results = []
        for row in X:
            age, bmi, avg_glucose_level, hypertension, heart_disease = row
            score = 0
            score += (age > 65) * 1
            score += (bmi > 30) * 1
            score += (avg_glucose_level > 140) * 1
            score += hypertension * 1
            score += heart_disease * 1

            if score <= 1:
                results.append("mild")
            elif score <= 3:
                results.append("moderate")
            else:
                results.append("severe")
        return np.array(results)

    def predict_proba(self, X: np.ndarray):
        preds = self.predict(X)
        proba = []
        for p in preds:
            if p == "mild":
                proba.append([0.7, 0.2, 0.1])
            elif p == "moderate":
                proba.append([0.1, 0.7, 0.2])
            else:
                proba.append([0.1, 0.2, 0.7])
        return np.array(proba)


if gradient_boosting_model is not None:
    ACTIVE_MODEL_NAME = "gradient_boosting"
    ACTIVE_MODEL = gradient_boosting_model
elif decision_tree_model is not None:
    ACTIVE_MODEL_NAME = "decision_tree"
    ACTIVE_MODEL = decision_tree_model
else:
    ACTIVE_MODEL_NAME = "fallback_rule_based"
    ACTIVE_MODEL = SimpleFallbackModel()


@router.get("/health")
def health_check():
    return {"status": "ok", "model": ACTIVE_MODEL_NAME}


@router.post(
    "/predict",
    response_model=schemas.PredictionResponse,
    status_code=status.HTTP_200_OK,
)
def predict(
    payload: schemas.PredictionRequest,
    db: Annotated[Session, Depends(get_db)],
):
    features = np.array(
        [
            [
                payload.age,
                payload.bmi,
                payload.avg_glucose_level,
                payload.hypertension,
                payload.heart_disease,
            ]
        ]
    )

    y_pred = ACTIVE_MODEL.predict(features)[0]

    probabilities = None
    if hasattr(ACTIVE_MODEL, "predict_proba"):
        proba = ACTIVE_MODEL.predict_proba(features)[0]
        class_labels = getattr(ACTIVE_MODEL, "classes_", None)
        if class_labels is not None:
            probabilities = {
                str(cls): float(p) for cls, p in zip(class_labels, proba)
            }

    severity = str(y_pred)

    record = Prediction(
        age=payload.age,
        bmi=payload.bmi,
        avg_glucose_level=payload.avg_glucose_level,
        hypertension=payload.hypertension,
        heart_disease=payload.heart_disease,
        severity=severity,
        model=ACTIVE_MODEL_NAME,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return schemas.PredictionResponse(
        prediction_id=record.id,
        severity=severity,
        model=ACTIVE_MODEL_NAME,
        probabilities=probabilities,
    )


@router.get(
    "/predictions",
    response_model=schemas.PredictionListResponse,
)
def list_predictions(
    limit: int = 50,
    offset: int = 0,
    db: Annotated[Session, Depends(get_db)] = None,
):
    query = db.query(Prediction).order_by(Prediction.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return schemas.PredictionListResponse(items=items, total=total)


@router.get(
    "/predictions/{prediction_id}",
    response_model=schemas.PredictionRecord,
)
def get_prediction(
    prediction_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
):
    record = (
        db.query(Prediction)
        .filter(Prediction.id == prediction_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )
    return record

