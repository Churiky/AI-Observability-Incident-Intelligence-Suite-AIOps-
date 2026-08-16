"""
Model training script for training anomaly detection and classification models.
"""
import argparse
import logging
import os
import json
from datetime import datetime, timedelta
import numpy as np
from app.models.database import *
from app.models.schemas import *
from app.services.anomaly_detector import AnomalyDetector
from app.services.severity_classifier import SeverityClassifier
from app.services.feature_engineering import FeatureEngineeringService
from app.core.database import SessionLocal
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    return SessionLocal()


def train_anomaly_detector(db: Session):
    """Train the anomaly detection model on historical data."""
    logger.info("Starting anomaly detection model training...")

    # Get historical anomalies and normal logs for training
    # In a real implementation, we would have labeled data
    # For now, we'll use a mix of high and low anomaly score logs

    # Get logs with high anomaly scores (likely anomalies)
    high_anomaly_logs = db.query(Log).filter(Log.anomaly_score >= 0.7).limit(1000).all()

    # Get logs with low anomaly scores (likely normal)
    low_anomaly_logs = db.query(Log).filter(Log.anomaly_score < 0.3).limit(1000).all()

    # Combine for training
    training_logs = high_anomaly_logs + low_anomaly_logs

    if len(training_logs) < 20:
        logger.warning("Insufficient data for training anomaly detector. Need at least 20 samples.")
        return False

    # Convert to LogCreate format for the detector
    from app.models.schemas import LogCreate, LogLevel
    training_data = []
    for log in training_logs:
        try:
            log_create = LogCreate(
                timestamp=log.timestamp,
                service=log.service.name if log.service else "unknown",
                host=log.host,
                level=LogLevel(log.level) if log.level in [l.value for l in LogLevel] else LogLevel.INFO,
                message=log.message,
                request_id=log.request_id,
                status_code=log.status_code,
                latency_ms=log.latency_ms,
                endpoint=log.endpoint,
                exception_type=log.exception_type,
                environment=log.environment
            )
            training_data.append(log_create)
        except Exception as e:
            logger.warning(f"Skipping log due to conversion error: {e}")
            continue

    if len(training_data) < 10:
        logger.warning("Insufficient valid data for training after conversion.")
        return False

    # Train the anomaly detector
    detector = AnomalyDetector()
    try:
        detector.train_model(training_data)
        logger.info(f"Anomaly detector trained successfully on {len(training_data)} samples")
        return True
    except Exception as e:
        logger.error(f"Error training anomaly detector: {e}")
        return False


def train_severity_classifier(db: Session):
    """Train the severity classification model on historical incident data."""
    logger.info("Starting severity classification model training...")

    # Get incidents with known severity (not PENDING)
    incidents = db.query(Incident).filter(
        Incident.severity.in_(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    ).all()

    if len(incidents) < 10:
        logger.warning("Insufficient labeled incidents for training severity classifier. Need at least 10.")
        return False

    # Train the severity classifier
    classifier = SeverityClassifier(db)
    try:
        classifier.train_model(incidents)
        logger.info(f"Severity classifier trained successfully on {len(incidents)} samples")
        return True
    except Exception as e:
        logger.error(f"Error training severity classifier: {e}")
        return False


def generate_training_data(db: Session):
    """
    Generate synthetic training data for initial model training.
    This would be used when there's insufficient real data.
    """
    logger.info("Generating synthetic training data...")

    # This is a placeholder - in a real implementation, we would:
    # 1. Generate synthetic logs with known anomalies
    # 2. Label them appropriately
    # 3. Use them to train initial models

    logger.info("Synthetic data generation not implemented in this version")
    return False


def main():
    parser = argparse.ArgumentParser(description="Train ML models for the observability platform")
    parser.add_argument("--anomaly-detector", action="store_true",
                        help="Train anomaly detection model")
    parser.add_argument("--severity-classifier", action="store_true",
                        help="Train severity classification model")
    parser.add_argument("--generate-data", action="store_true",
                        help="Generate synthetic training data")
    parser.add_argument("--all", action="store_true",
                        help="Train all models")

    args = parser.parse_args()

    if not any([args.anomaly_detector, args.severity_classifier, args.generate_data, args.all]):
        # Default to training all if nothing specified
        args.all = True

    db = get_db_session()
    try:
        success = True

        if args.all or args.anomaly_detector:
            if not train_anomaly_detector(db):
                success = False

        if args.all or args.severity_classifier:
            if not train_severity_classifier(db):
                success = False

        if args.all or args.generate_data:
            if not generate_training_data(db):
                success = False

        if success:
            logger.info("All requested training completed successfully")
        else:
            logger.error("Some training operations failed")
            return 1

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    exit(main())