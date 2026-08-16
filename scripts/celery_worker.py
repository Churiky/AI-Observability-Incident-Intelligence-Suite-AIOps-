"""
Celery worker for background jobs:
- incident_clustering: Groups temporal and semantically related anomalies into incidents
- severity_prediction: Runs Random Forest severity classifier on incident features
- incident_ai_analysis: Generates RAG prompt, retrieves similar historical incidents, queries Ollama
"""
import json
import logging
from typing import List, Optional
from celery import Celery
from app.core.config import settings
from app.models.database import *
from app.models.schemas import *
from app.services.incident_correlator import IncidentCorrelator
from app.services.severity_classifier import SeverityClassifier
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "observability_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


def get_db_session() -> Session:
    """Get a database session."""
    return SessionLocal()


@celery_app.task(bind=True)
def incident_clustering(self, anomaly_ids: List[int]):
    """
    Group temporal and semantically related anomalies into incidents using local FAISS vector matching.
    """
    try:
        logger.info(f"Starting incident clustering for {len(anomaly_ids)} anomalies")
        db = get_db_session()
        try:
            correlator = IncidentCorrelator(db)
            incidents_created = correlator.cluster_anomalies(anomaly_ids)
            logger.info(f"Created {len(incidents_created)} incidents from clustering")
            return {"incidents_created": len(incidents_created), "incident_ids": [i.id for i in incidents_created]}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in incident clustering: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def severity_prediction(self, incident_id: int):
    """
    Run Random Forest severity classifier on incident features.
    """
    try:
        logger.info(f"Starting severity prediction for incident {incident_id}")
        db = get_db_session()
        try:
            classifier = SeverityClassifier(db)
            severity_result = classifier.predict_severity(incident_id)
            logger.info(f"Severity prediction for incident {incident_id}: {severity_result}")
            return severity_result
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in severity prediction: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def incident_ai_analysis(self, incident_id: int):
    """
    Generate RAG prompt, retrieve top 3 similar historical incidents using FAISS,
    query Ollama (local LLM), and save the report.
    """
    try:
        logger.info(f"Starting AI analysis for incident {incident_id}")
        db = get_db_session()
        try:
            rag_service = RAGService(db)
            llm_service = LLMService()

            # Generate investigation report
            report = llm_service.generate_incident_report(
                incident_id=incident_id,
                rag_service=rag_service
            )

            # Save report to database
            from app.models.database import AIReport
            ai_report = AIReport(
                incident_id=incident_id,
                report_markdown=report,
                generated_at=datetime.utcnow()
            )
            db.add(ai_report)
            db.commit()

            logger.info(f"AI analysis completed for incident {incident_id}")
            return {"incident_id": incident_id, "report_generated": True}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


# Health check task
@celery_app.task
def health_check():
    """Simple health check task."""
    return {"status": "healthy", "worker": "celery"}


if __name__ == "__main__":
    celery_app.start()