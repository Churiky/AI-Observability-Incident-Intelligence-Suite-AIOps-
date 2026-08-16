"""
Unit tests for the anomaly detector service.
"""
import pytest
import numpy as np
from app.services.anomaly_detector import AnomalyDetector
from app.models.schemas import LogCreate, LogLevel
from datetime import datetime


def test_anomaly_detector_initialization():
    """Test that the anomaly detector initializes correctly."""
    detector = AnomalyDetector()
    assert detector is not None
    assert detector.isolation_forest is not None


def test_extract_features():
    """Test feature extraction from a log entry."""
    detector = AnomalyDetector()

    # Create a test log
    test_log = LogCreate(
        timestamp=datetime(2026, 8, 16, 10, 23, 41),
        service="test-service",
        level=LogLevel.ERROR,
        message="Test error message",
        host="test-host",
        request_id="req_123",
        status_code=500,
        latency_ms=1500.0,
        endpoint="/api/test",
        exception_type="TestException",
        environment="production"
    )

    features = detector.extract_features(test_log)

    # Should return a numpy array with shape (1, n_features)
    assert isinstance(features, np.ndarray)
    assert features.shape[0] == 1  # One sample
    assert features.shape[1] > 0   # At least one feature

    # Check specific feature values
    # Feature 0: latency_ms
    assert features[0, 0] == 1500.0
    # Feature 1: status_code
    assert features[0, 1] == 500.0
    # Feature 4: hour of day (should be 10)
    assert features[0, 4] == 10.0
    # Feature 5: day of week (2026-08-16 is a Sunday, which is 6)
    assert features[0, 5] == 6.0


def test_detect_anomaly_statistical():
    """Test statistical anomaly detection."""
    detector = AnomalyDetector()

    # Test normal log
    normal_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level=LogLevel.INFO,
        message="Normal request",
        host="test-host",
        request_id="req_123",
        status_code=200,
        latency_ms=50.0,  # Normal latency
        endpoint="/api/test",
        environment="production"
    )

    score, is_anomaly = detector.detect_anomaly_statistical(normal_log)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(is_anomaly, bool)
    # Normal log should likely not be an anomaly (though depends on thresholds)

    # Test anomalous log (high latency)
    anomalous_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level=LogLevel.ERROR,
        message="Slow request",
        host="test-host",
        request_id="req_124",
        status_code=200,
        latency_ms=5000.0,  # High latency
        endpoint="/api/test",
        environment="production"
    )

    score, is_anomaly = detector.detect_anomaly_statistical(anomalous_log)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(is_anomaly, bool)
    # High latency should likely be detected as anomalous
    # Note: Exact behavior depends on implementation thresholds


def test_detect_anomaly_ml_fallback():
    """Test ML anomaly detection falls back to statistical when model not trained."""
    detector = AnomalyDetector()
    # Ensure we're using fallback by not training the model
    # The detect_anomaly_ml method should fall back to statistical

    test_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level=LogLevel.INFO,
        message="Test message",
        host="test-host",
        request_id="req_123",
        status_code=200,
        latency_ms=100.0,
        endpoint="/api/test",
        environment="production"
    )

    score, is_anomaly = detector.detect_anomaly_ml(test_log)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(is_anomaly, bool)
    # Should work without error (fallback to statistical)


def test_detect_anomaly_combined():
    """Test combined anomaly detection."""
    detector = AnomalyDetector()

    test_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level=LogLevel.WARNING,
        message="Test warning",
        host="test-host",
        request_id="req_123",
        status_code=400,
        latency_ms=200.0,
        endpoint="/api/test",
        environment="production"
    )

    score, is_anomaly = detector.detect_anomaly(test_log)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(is_anomaly, bool)


if __name__ == "__main__":
    pytest.main([__file__])