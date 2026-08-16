"""
Pydantic schemas for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogBase(BaseModel):
    timestamp: datetime
    service: str
    host: Optional[str] = None
    level: LogLevel
    message: str
    request_id: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    endpoint: Optional[str] = None
    exception_type: Optional[str] = None
    environment: Optional[str] = None
    anomaly_score: Optional[float] = None
    is_anomaly: bool = False


class LogCreate(LogBase):
    pass


class LogResponse(LogBase):
    id: int

    class Config:
        from_attributes = True


class IncidentBase(BaseModel):
    title: str
    severity: str
    status: str = "ACTIVE"
    incident_score: Optional[float] = None
    root_cause: Optional[str] = None
    confidence: Optional[float] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentResponse(IncidentBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyBase(BaseModel):
    service_id: int
    timestamp: datetime
    message: str
    level: LogLevel
    latency_ms: Optional[float] = None
    anomaly_score: float
    request_id: Optional[str] = None


class AnomalyCreate(AnomalyBase):
    pass


class AnomalyResponse(AnomalyBase):
    id: int

    class Config:
        from_attributes = True


class SeverityPrediction(BaseModel):
    severity: str
    confidence: float
    important_features: List[dict] = []


class AIInvestigationRequest(BaseModel):
    incident_id: int


class AIInvestigationResponse(BaseModel):
    incident_id: int
    summary: str
    impact: str
    probable_cause: str
    recommended_investigation: List[str]
    confidence: str  # Confirmed, Probable, Possible, Unknown