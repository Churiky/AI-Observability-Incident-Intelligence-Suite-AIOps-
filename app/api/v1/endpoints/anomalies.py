"""
Anomaly endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.schemas import AnomalyCreate, AnomalyResponse, LogLevel

router = APIRouter()

# Mock data for demonstration - aligned with schemas
MOCK_ANOMALIES = [
    {
        "id": 1,
        "service_id": 1,
        "timestamp": datetime.now() - timedelta(minutes=5),
        "message": "High response time detected",
        "level": LogLevel.WARNING,
        "latency_ms": 2300.5,
        "anomaly_score": 0.87,
        "request_id": "req-12345"
    },
    {
        "id": 2,
        "service_id": 2,
        "timestamp": datetime.now() - timedelta(minutes=15),
        "message": "Error rate spike",
        "level": LogLevel.ERROR,
        "latency_ms": 45.2,
        "anomaly_score": 0.92,
        "request_id": "req-12346"
    },
    {
        "id": 3,
        "service_id": 1,
        "timestamp": datetime.now() - timedelta(minutes=30),
        "message": "CPU usage threshold exceeded",
        "level": LogLevel.INFO,
        "latency_ms": 120.0,
        "anomaly_score": 0.75,
        "request_id": "req-12347"
    }
]

@router.get("/", response_model=List[AnomalyResponse])
async def get_anomalies(
    skip: int = 0,
    limit: int = 100,
    service_id: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """
    Retrieve anomalies with optional filtering.
    """
    filtered = MOCK_ANOMALIES
    if service_id:
        filtered = [anom for anom in filtered if anom["service_id"] == service_id]
    # Simplified time filtering for demo
    if start_time:
        filtered = [anom for anom in filtered if anom["timestamp"] >= start_time]
    if end_time:
        filtered = [anom for anom in filtered if anom["timestamp"] <= end_time]
    return filtered[skip:skip+limit]

@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(anomaly_id: int):
    """
    Get a specific anomaly by ID.
    """
    for anomaly in MOCK_ANOMALIES:
        if anomaly["id"] == anomaly_id:
            return anomaly
    raise HTTPException(status_code=404, detail="Anomaly not found")

@router.post("/", response_model=AnomalyResponse)
async def create_anomaly(anomaly: AnomalyCreate):
    """
    Create a new anomaly.
    """
    new_id = max([anom["id"] for anom in MOCK_ANOMALIES]) + 1 if MOCK_ANOMALIES else 1
    new_anomaly = {
        "id": new_id,
        **anomaly.dict()
    }
    MOCK_ANOMALIES.append(new_anomaly)
    return new_anomaly