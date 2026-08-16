"""
Unit tests for the incident correlator service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.services.incident_correlator import IncidentCorrelator
from app.models.database import *
from app.models.schemas import *
from datetime import datetime, timedelta


def test_incident_correlator_initialization():
    """Test that the incident correlator initializes correctly."""
    mock_db = Mock()
    correlator = IncidentCorrelator(mock_db)
    assert correlator is not None
    assert correlator.db == mock_db


def test_group_by_temporal_window():
    """Test temporal window grouping logic."""
    mock_db = Mock()
    correlator = IncidentCorrelator(mock_db)

    # Create test anomalies with specific timestamps
    base_time = datetime(2026, 8, 16, 10, 0, 0)

    anomaly1 = Mock(spec=Anomaly)
    anomaly1.timestamp = base_time

    anomaly2 = Mock(spec=Anomaly)
    anomaly2.timestamp = base_time + timedelta(minutes=2)  # Within 5 minute window

    anomaly3 = Mock(spec=Anomaly)
    anomaly3.timestamp = base_time + timedelta(minutes=10)  # Outside 5 minute window

    anomalies = [anomaly1, anomaly2, anomaly3]

    # Test with 5 minute window
    groups = correlator._group_by_temporal_window(anomalies, window_minutes=5)

    # Should have 2 groups: [anomaly1, anomaly2] and [anomaly3]
    assert len(groups) == 2
    assert len(groups[0]) == 2  # First group has 2 anomalies
    assert len(groups[1]) == 1  # Second group has 1 anomaly
    assert groups[0][0] == anomaly1
    assert groups[0][1] == anomaly2
    assert groups[1][0] == anomaly3


def test_group_by_temporal_window_empty():
    """Test temporal window grouping with empty list."""
    mock_db = Mock()
    correlator = IncidentCorrelator(mock_db)

    groups = correlator._group_by_temporal_window([], window_minutes=5)
    assert groups == []


def test_group_by_temporal_window_single():
    """Test temporal window grouping with single anomaly."""
    mock_db = Mock()
    correlator = IncidentCorrelator(mock_db)

    anomaly = Mock(spec=Anomaly)
    anomaly.timestamp = datetime.utcnow()

    groups = correlator._group_by_temporal_window([anomaly], window_minutes=5)
    assert len(groups) == 1
    assert len(groups[0]) == 1
    assert groups[0][0] == anomaly


def test_generate_incident_title():
    """Test incident title generation."""
    mock_db = Mock()
    correlator = IncidentCorrelator(mock_db)

    # Create a mock anomaly
    anomaly = Mock(spec=Anomaly)
    anomaly.service = Mock()
    anomaly.service.name = "payment-service"
    anomaly.level = Mock()
    anomaly.level.value = "ERROR"
    anomaly.message = "Database connection timeout occurred"

    title = correlator._generate_incident_title(anomaly)
    assert "payment-service" in title
    assert "Database Issue" in title  # Because message contains "database"

    # Test with CPU message
    anomaly.message = "CPU usage spike detected"
    title = correlator._generate_incident_title(anomaly)
    assert "CPU Spike" in title

    # Test with network message
    anomaly.message = "Network connection failed"
    title = correlator._generate_incident_title(anomaly)
    assert "Network Issue" in title

    # Test with generic message
    anomaly.message = "Something happened"
    title = correlator._generate_incident_title(anomaly)
    assert "payment-service" in title
    assert "ERROR Incident" in title


if __name__ == "__main__":
    pytest.main([__file__])