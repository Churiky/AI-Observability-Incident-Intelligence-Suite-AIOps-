"""
Prediction endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import SeverityPrediction

router = APIRouter()

# Mock data for demonstration - aligned with SeverityPrediction schema
MOCK_PREDICTIONS = [
    {
        "severity": "HIGH",
        "confidence": 0.85,
        "important_features": [
            {"feature": "response_time_increase", "importance": 0.3},
            {"feature": "error_rate_spike", "importance": 0.25},
            {"feature": "connection_pool_usage", "importance": 0.2}
        ]
    },
    {
        "severity": "MEDIUM",
        "confidence": 0.72,
        "important_features": [
            {"feature": "memory_trend", "importance": 0.4},
            {"feature": "gc_pause_increase", "importance": 0.35}
        ]
    }
]

@router.get("/", response_model=List[SeverityPrediction])
async def get_predictions(
    incident_id: Optional[int] = Query(None),
    limit: int = 100
):
    """
    Retrieve severity predictions.
    """
    # In a real implementation, we would filter by incident_id
    return MOCK_PREDICTIONS[:limit]

@router.post("/", response_model=SeverityPrediction)
async def create_prediction():
    """
    Create a new severity prediction (simplified).
    """
    # Return a mock prediction
    return {
        "severity": "HIGH",
        "confidence": 0.8,
        "important_features": [
            {"feature": "predicted_factor_1", "importance": 0.3},
            {"feature": "predicted_factor_2", "importance": 0.25}
        ]
    }