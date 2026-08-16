"""
Severity classification service using machine learning.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from app.models.database import *
from app.models.schemas import *
from app.services.feature_engineering import FeatureEngineeringService
import logging

logger = logging.getLogger(__name__)


class SeverityClassifier:
    def __init__(self, db_session):
        self.db = db_session
        self.feature_service = FeatureEngineeringService(db_session)
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "./ml/artifacts/severity_classifier_model.joblib"
        self.scaler_path = "./ml/artifacts/severity_scaler.joblib"
        self.severity_labels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.label_to_int = {label: i for i, label in enumerate(self.severity_labels)}
        self.int_to_label = {i: label for i, label in enumerate(self.severity_labels)}
        self._load_or_create_model()

    def _load_or_create_model(self):
        """Load existing model or create a new one."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing severity classification model")
            else:
                # Create new model
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                logger.info("Created new severity classification model")
        except Exception as e:
            logger.warning(f"Error loading model: {e}. Creating new model.")
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )

    def predict_severity(self, incident_id: int) -> Dict[str, Any]:
        """
        Predict severity for an incident using Random Forest classifier.
        Returns prediction with confidence and feature importance.
        """
        try:
            # Get incident and its anomalies
            incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
            if not incident:
                raise ValueError(f"Incident {incident_id} not found")

            # Extract features from incident
            features = self._extract_incident_features(incident)

            if self.model is None:
                # Fallback to rule-based classification
                return self._rule_based_severity(incident)

            # Scale features
            features_scaled = self.scaler.transform([features])

            # Predict
            prediction_int = self.model.predict(features_scaled)[0]
            prediction_proba = self.model.predict_proba(features_scaled)[0]

            # Get predicted severity and confidence
            predicted_severity = self.int_to_label[prediction_int]
            confidence = float(max(prediction_proba))

            # Get feature importance
            feature_names = self._get_feature_names()
            important_features = []
            if hasattr(self.model, 'feature_importances_'):
                for i, importance in enumerate(self.model.feature_importances_):
                    if importance > 0.01:  # Only include significant features
                        important_features.append({
                            "feature": feature_names[i] if i < len(feature_names) else f"feature_{i}",
                            "importance": float(importance)
                        })

            # Update incident in database
            incident.severity = predicted_severity
            # Calculate incident score (simplified)
            incident.incident_score = self._calculate_incident_score(incident, confidence)
            self.db.commit()

            result = {
                "incident_id": incident_id,
                "severity": predicted_severity,
                "confidence": confidence,
                "important_features": important_features
            }

            logger.info(f"Severity prediction for incident {incident_id}: {predicted_severity} (confidence: {confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error in severity prediction: {e}")
            # Fallback to rule-based
            return self._rule_based_severity(incident if 'incident' in locals() else None)

    def _extract_incident_features(self, incident: Incident) -> np.ndarray:
        """Extract numerical features from an incident for severity classification."""
        features = []

        # Incident-level features
        # 1. Number of anomalies
        features.append(len(incident.anomalies))

        # 2. Average anomaly score
        if incident.anomalies:
            avg_anomaly_score = np.mean([a.anomaly_score for a in incident.anomalies])
            features.append(avg_anomaly_score)
        else:
            features.append(0.0)

        # 3. Max anomaly score
        if incident.anomalies:
            max_anomaly_score = np.max([a.anomaly_score for a in incident.anomalies])
            features.append(max_anomaly_score)
        else:
            features.append(0.0)

        # 4. Time span of anomalies (in minutes)
        if len(incident.anomalies) >= 2:
            timestamps = [a.timestamp for a in incident.anomalies]
            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
            features.append(min(time_span, 60))  # Cap at 60 minutes
        else:
            features.append(0.0)

        # 5. Unique services affected
        unique_services = len(set([a.service.id for a in incident.anomalies if a.service]))
        features.append(unique_services)

        # 6. Log level distribution (encoded)
        level_counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        for anomaly in incident.anomalies:
            level = anomaly.level.value if hasattr(anomaly.level, 'value') else str(anomaly.level)
            if level in level_counts:
                level_counts[level] += 1

        total_anomalies = len(incident.anomalies) if incident.anomalies else 1
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            features.append(level_counts[level] / total_anomalies)

        # 7. Average latency
        latencies = [a.latency_ms for a in incident.anomalies if a.latency_ms is not None]
        if latencies:
            features.append(np.mean(latencies))
        else:
            features.append(0.0)

        # 8. Error rate (percentage of ERROR/CRITICAL logs)
        error_critical_count = sum(1 for a in incident.anomalies
                                  if a.level.value if hasattr(a.level, 'value') else str(a.level) in ["ERROR", "CRITICAL"])
        if incident.anomalies:
            features.append(error_critical_count / len(incident.anomalies))
        else:
            features.append(0.0)

        return np.array(features)

    def _get_feature_names(self) -> List[str]:
        """Get names of features for interpretability."""
        return [
            "anomaly_count",
            "avg_anomaly_score",
            "max_anomaly_score",
            "time_span_minutes",
            "unique_services",
            "pct_debug",
            "pct_info",
            "pct_warning",
            "pct_error",
            "pct_critical",
            "avg_latency",
            "error_rate"
        ]

    def _rule_based_severity(self, incident: Incident) -> Dict[str, Any]:
        """Fallback rule-based severity classification."""
        if not incident:
            return {"severity": "UNKNOWN", "confidence": 0.0, "important_features": []}

        # Simple rule-based approach
        score = 0.0
        factors = []

        # Factor 1: Number of anomalies
        anomaly_count = len(incident.anomalies)
        if anomaly_count >= 10:
            score += 0.3
            factors.append(("high_anomaly_count", 0.3))
        elif anomaly_count >= 5:
            score += 0.2
            factors.append(("medium_anomaly_count", 0.2))
        elif anomaly_count >= 2:
            score += 0.1
            factors.append(("low_anomaly_count", 0.1))

        # Factor 2: Average anomaly score
        if incident.anomalies:
            avg_score = np.mean([a.anomaly_score for a in incident.anomalies])
            score += min(avg_score * 0.4, 0.4)  # Max 0.4 from anomaly score
            factors.append(("anomaly_score", min(avg_score * 0.4, 0.4)))

        # Factor 3: Presence of CRITICAL logs
        critical_count = sum(1 for a in incident.anomalies
                            if a.level.value if hasattr(a.level, 'value') else str(a.level) == "CRITICAL")
        if critical_count > 0:
            score += 0.3
            factors.append(("critical_logs", 0.3))

        # Factor 4: Unique services
        unique_services = len(set([a.service.id for a in incident.anomalies if a.service]))
        if unique_services >= 3:
            score += 0.2
            factors.append(("multiple_services", 0.2))
        elif unique_services >= 2:
            score += 0.1
            factors.append(("two_services", 0.1))

        # Normalize score to 0-1 range
        score = min(score, 1.0)

        # Map score to severity
        if score >= 0.8:
            severity = "CRITICAL"
        elif score >= 0.6:
            severity = "HIGH"
        elif score >= 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        confidence = min(score + 0.2, 0.95)  # Simple confidence estimate

        # Update incident
        incident.severity = severity
        incident.incident_score = score
        self.db.commit()

        important_features = [{"feature": name, "importance": val}
                             for name, val in factors]

        return {
            "incident_id": incident.id,
            "severity": severity,
            "confidence": confidence,
            "important_features": important_features
        }

    def _calculate_incident_score(self, incident: Incident, confidence: float) -> float:
        """Calculate incident score based on various factors."""
        # Simplified incident score calculation
        factors = []

        # Anomaly count factor (0-0.3)
        anomaly_count = len(incident.anomalies)
        anomaly_factor = min(anomaly_count / 20.0, 0.3)
        factors.append(anomaly_factor)

        # Average anomaly score factor (0-0.3)
        if incident.anomalies:
            avg_anomaly_score = np.mean([a.anomaly_score for a in incident.anomalies])
            anomaly_score_factor = avg_anomaly_score * 0.3
            factors.append(anomaly_score_factor)
        else:
            factors.append(0.0)

        # Confidence factor (0-0.2)
        confidence_factor = confidence * 0.2
        factors.append(confidence_factor)

        # Service spread factor (0-0.2)
        unique_services = len(set([a.service.id for a in incident.anomalies if a.service]))
        service_factor = min(unique_services / 5.0, 0.2)
        factors.append(service_factor)

        return min(sum(factors), 1.0)

    def train_model(self, incidents: List[Incident]):
        """
        Train the Random Forest model on historical incident data.
        This would require labeled data (incidents with known severity).
        """
        if len(incidents) < 10:
            logger.warning("Need at least 10 labeled incidents to train the model")
            return

        # Extract features and labels
        features = []
        labels = []

        for incident in incidents:
            if incident.severity in self.severity_labels:
                feature_vector = self._extract_incident_features(incident)
                features.append(feature_vector)
                labels.append(self.label_to_int[incident.severity])

        if len(features) < 10:
            logger.warning("Not enough labeled data to train model")
            return

        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(labels)

        # Fit scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Train model
        self.model.fit(X_scaled, y)

        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        logger.info(f"Trained severity classification model on {len(incidents)} incidents")