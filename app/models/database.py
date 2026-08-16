"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


Base = declarative_base()


# Association table for incident-anomaly many-to-many relationship
incident_anomalies = Table(
    'incident_anomalies',
    Base.metadata,
    Column('incident_id', Integer, ForeignKey('incidents.id'), primary_key=True),
    Column('anomaly_id', Integer, ForeignKey('anomalies.id'), primary_key=True)
)


# Log model (for storing anomalies and incidents only - normal logs are discarded)
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    message = Column(Text, nullable=False)
    level = Column(String)
    host = Column(String)
    request_id = Column(String, index=True)
    status_code = Column(Integer)
    latency_ms = Column(Float)
    endpoint = Column(String)
    exception_type = Column(String)
    environment = Column(String)
    anomaly_score = Column(Float)
    is_anomaly = Column(Boolean, default=False)

    # Relationships
    service = relationship("Service")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    environment = Column(String, default="production")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    metrics = relationship("MetricsHourly", back_populates="service")
    anomalies = relationship("Anomaly", back_populates="service")


class MetricsHourly(Base):
    __tablename__ = "metrics_hourly"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_pct = Column(Float)
    memory_pct = Column(Float)
    error_rate = Column(Float)
    latency_p95 = Column(Float)

    # Relationships
    service = relationship("Service", back_populates="metrics")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    message = Column(Text, nullable=False)
    level = Column(String)
    latency_ms = Column(Float)
    anomaly_score = Column(Float, nullable=False)
    request_id = Column(String, index=True)

    # Relationships
    service = relationship("Service", back_populates="anomalies")
    incidents = relationship("Incident", secondary=incident_anomalies, back_populates="anomalies")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="ACTIVE")  # ACTIVE, RESOLVED
    incident_score = Column(Float)
    root_cause = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    anomalies = relationship("Anomaly", secondary=incident_anomalies, back_populates="incidents")
    ai_reports = relationship("AIReport", back_populates="incident")


class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    report_markdown = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    incident = relationship("Incident", back_populates="ai_reports")