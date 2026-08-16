"""
Anomaly detection service implementing statistical and ML-based approaches.
"""
import numpy as np
from typing import List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from app.core.config import settings
from app.models.schemas import LogCreate
from app.models.database import Log
from sqlalchemy.orm import Session


class AnomalyDetector:
    def __init__(self):
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.model_path = "./ml/artifacts/isolation_forest_model.joblib"
        self.scaler_path = "./ml/artifacts/scaler.joblib"
        self._load_or_create_models()

    def _load_or_create_models(self):
        """Load existing models or create new ones."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.isolation_forest = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
            else:
                # Create new models
                self.isolation_forest = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        except Exception as e:
            # Fallback to creating new models
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )

    def extract_features(self, log: LogCreate) -> np.ndarray:
        """
        Extract numerical features from a log entry for anomaly detection.
        Features include:
        - Latency (if available)
        - Status code (if available)
        - Service-specific features (hashed)
        - Time-based features
        - Level encoding
        """
        features = []

        # Latency feature
        features.append(log.latency_ms if log.latency_ms is not None else 0.0)

        # Status code feature
        features.append(float(log.status_code) if log.status_code is not None else 0.0)

        # Service feature (simple hash)
        service_hash = hash(log.service) % 1000
        features.append(float(service_hash))

        # Level encoding
        level_mapping = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        features.append(float(level_mapping.get(log.level.value if hasattr(log.level, 'value') else str(log.level), 1)))

        # Hour of day (from timestamp)
        if log.timestamp:
            features.append(float(log.timestamp.hour))
        else:
            features.append(0.0)

        # Day of week
        if log.timestamp:
            features.append(float(log.timestamp.weekday()))
        else:
            features.append(0.0)

        return np.array(features).reshape(1, -1)

    def detect_anomaly_statistical(self, log: LogCreate, recent_logs: List[LogCreate] = None) -> Tuple[float, bool]:
        """
        Detect anomalies using statistical methods (Z-score with rolling statistics).
        Returns: (anomaly_score, is_anomaly)
        """
        # This is a simplified implementation
        # In reality, we would maintain rolling statistics for each service/metric

        # For demonstration, we'll use a simple threshold-based approach
        anomaly_score = 0.0
        is_anomaly = False

        # Check latency
        if log.latency_ms is not None and log.latency_ms > 1000:  # > 1 second
            anomaly_score = max(anomaly_score, min(log.latency_ms / 2000, 1.0))
            is_anomaly = True

        # Check status code
        if log.status_code is not None and log.status_code >= 500:
            anomaly_score = max(anomaly_score, 0.8)
            is_anomaly = True
        elif log.status_code is not None and log.status_code >= 400:
            anomaly_score = max(anomaly_score, 0.5)
            is_anomaly = True

        # Check log level
        if log.level.value if hasattr(log.level, 'value') else str(log.level) in ["ERROR", "CRITICAL"]:
            anomaly_score = max(anomaly_score, 0.7)
            is_anomaly = True

        return anomaly_score, is_anomaly

    def detect_anomaly_ml(self, log: LogCreate) -> Tuple[float, bool]:
        """
        Detect anomalies using Machine Learning (Isolation Forest).
        Returns: (anomaly_score, is_anomaly)
        """
        if self.isolation_forest is None:
            # Fallback to statistical if ML model not ready
            return self.detect_anomaly_statistical(log)

        try:
            # Extract features
            features = self.extract_features(log)

            # Scale features
            features_scaled = self.scaler.transform(features)

            # Predict anomaly (-1 for anomaly, 1 for normal)
            prediction = self.isolation_forest.predict(features_scaled)[0]

            # Get anomaly score (negative values indicate anomalies)
            raw_score = self.isolation_forest.decision_function(features_scaled)[0]

            # Convert to 0-1 score where higher = more anomalous
            # Isolation Forest returns scores where lower = more anomalous
            anomaly_score = max(0.0, min(1.0, (0.5 - raw_score) * 2))
            is_anomaly = (prediction == -1)

            return anomaly_score, is_anomaly
        except Exception as e:
            # Fallback to statistical detection
            return self.detect_anomaly_statistical(log)

    def detect_anomaly(self, log: LogCreate, recent_logs: List[LogCreate] = None) -> Tuple[float, bool]:
        """
        Detect anomalies using both statistical and ML approaches.
        Returns combined result.
        """
        # Statistical detection
        stat_score, stat_anomaly = self.detect_anomaly_statistical(log, recent_logs)

        # ML detection
        ml_score, ml_anomaly = self.detect_anomaly_ml(log)

        # Combine scores (weighted average)
        combined_score = (stat_score * 0.4) + (ml_score * 0.6)

        # Consider it an anomaly if either method detects it
        is_anomaly = stat_anomaly or ml_anomaly

        return combined_score, is_anomaly

    def train_model(self, logs: List[LogCreate]):
        """
        Train the Isolation Forest model on historical data.
        """
        if len(logs) < 10:
            raise ValueError("Need at least 10 samples to train the model")

        # Extract features from all logs
        features = np.array([self.extract_features(log).flatten() for log in logs])

        # Fit scaler
        self.scaler.fit(features)

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Train Isolation Forest
        self.isolation_forest.fit(features_scaled)

        # Save models
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.isolation_forest, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)