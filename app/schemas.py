from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    age: float = Field(..., ge=0)
    bmi: float = Field(..., ge=0)
    avg_glucose_level: float = Field(..., ge=0)
    hypertension: int = Field(..., ge=0, le=1)
    heart_disease: int = Field(..., ge=0, le=1)


class PredictionResponse(BaseModel):
    prediction_id: int
    severity: str
    model: str
    probabilities: Optional[Dict[str, float]] = None


class PredictionRecord(BaseModel):
    id: int
    age: float
    bmi: float
    avg_glucose_level: float
    hypertension: int
    heart_disease: int
    severity: str
    model: str
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionListResponse(BaseModel):
    items: List[PredictionRecord]
    total: int

