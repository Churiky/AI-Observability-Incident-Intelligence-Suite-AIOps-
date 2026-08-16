"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock

# Set test environment variables
os.environ["TESTING"] = "1"
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_pass"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["SECRET_KEY"] = "test-secret-key"


@pytest.fixture
def mock_db_session():
    """Fixture providing a mock database session."""
    return Mock()


@pytest.fixture
def sample_log_create():
    """Fixture providing a sample LogCreate object."""
    from app.models.schemas import LogCreate, LogLevel
    from datetime import datetime

    return LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level=LogLevel.INFO,
        message="Test log message",
        host="test-host",
        request_id="req_123",
        status_code=200,
        latency_ms=50.0,
        endpoint="/test",
        exception_type=None,
        environment="test"
    )


@pytest.fixture
def sample_anomaly_create():
    """Fixture providing a sample AnomalyCreate object."""
    from app.models.schemas import AnomalyCreate, LogLevel
    from datetime import datetime

    return AnomalyCreate(
        service_id=1,
        timestamp=datetime.utcnow(),
        message="Test anomaly",
        level=LogLevel.WARNING,
        latency_ms=100.0,
        anomaly_score=0.8,
        request_id="req_456"
    )


@pytest.fixture
def sample_incident_create():
    """Fixture providing a sample IncidentCreate object."""
    from app.models.schemas import IncidentCreate
    from datetime import datetime

    return IncidentCreate(
        title="Test Incident",
        severity="HIGH",
        status="ACTIVE",
        incident_score=0.75,
        root_cause="Test root cause",
        confidence=0.85
    )


@pytest.fixture
def mock_fastapi_app():
    """Fixture providing a mock FastAPI app for testing."""
    from unittest.mock import Mock
    return Mock()


# Mark all tests in unit directory as unit tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )


# Mark all tests in integration directory as integration tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )