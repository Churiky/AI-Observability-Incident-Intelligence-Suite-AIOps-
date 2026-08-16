"""
Incident endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import IncidentCreate, IncidentResponse
from fastapi.encoders import jsonable_encoder
import redis.asyncio as redis
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock data for demonstration - aligned with schemas
MOCK_INCIDENTS = [
    {
        "id": 1,
        "title": "Database connection timeout",
        "severity": "HIGH",
        "status": "ACTIVE",
        "incident_score": 0.85,
        "root_cause": "Connection pool exhaustion",
        "confidence": 0.9,
        "created_at": datetime.now(),
        "resolved_at": None
    },
    {
        "id": 2,
        "title": "Memory leak in service-b",
        "severity": "MEDIUM",
        "status": "INVESTIGATING",
        "incident_score": 0.65,
        "root_cause": None,
        "confidence": 0.7,
        "created_at": datetime.now(),
        "resolved_at": None
    }
]

@router.get("/", response_model=List[IncidentResponse])
async def get_incidents(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    Retrieve incidents with optional filtering.
    """
    filtered = MOCK_INCIDENTS
    if severity:
        filtered = [inc for inc in filtered if inc["severity"] == severity.upper()]
    if status:
        filtered = [inc for inc in filtered if inc["status"] == status.upper()]
    return filtered[skip:skip+limit]

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int):
    """
    Get a specific incident by ID.
    """
    for incident in MOCK_INCIDENTS:
        if incident["id"] == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")

@router.post("/", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate):
    """
    Create a new incident.
    """
    new_id = max([inc["id"] for inc in MOCK_INCIDENTS]) + 1 if MOCK_INCIDENTS else 1
    new_incident = {
        "id": new_id,
        **incident.dict(),
        "incident_score": 0.5,  # Default score
        "created_at": datetime.now(),
        "resolved_at": None
    }
    MOCK_INCIDENTS.append(new_incident)

    # Publish to Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.publish(
            "incident-updates",
            json.dumps({
                "channel": "incident-updates",
                "event": "incident_created",
                "data": jsonable_encoder(new_incident)
            })
        )
        await redis_client.close()
    except Exception as e:
        logger.error(f"Failed to publish incident_created event to Redis: {e}")

    return new_incident

@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: int, incident: IncidentCreate):
    """
    Update an existing incident.
    """
    for i, inc in enumerate(MOCK_INCIDENTS):
        if inc["id"] == incident_id:
            updated = {
                "id": incident_id,
                **incident.dict(),
                "incident_score": inc["incident_score"],  # Keep existing score
                "created_at": inc["created_at"],
                "resolved_at": inc["resolved_at"]
            }
            MOCK_INCIDENTS[i] = updated

            # Publish to Redis
            try:
                redis_client = redis.from_url(settings.REDIS_URL)
                await redis_client.publish(
                    "incident-updates",
                    json.dumps({
                        "channel": "incident-updates",
                        "event": "incident_updated",
                        "data": jsonable_encoder(updated)
                    })
                )
                await redis_client.close()
            except Exception as e:
                logger.error(f"Failed to publish incident_updated event to Redis: {e}")

            return updated
    raise HTTPException(status_code=404, detail="Incident not found")

@router.delete("/{incident_id}")
async def delete_incident(incident_id: int):
    """
    Delete an incident.
    """
    global MOCK_INCIDENTS
    MOCK_INCIDENTS = [inc for inc in MOCK_INCIDENTS if inc["id"] != incident_id]
    return {"message": "Incident deleted"}