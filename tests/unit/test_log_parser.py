"""
Unit tests for the log parser service.
"""
import pytest
from app.services.log_parser import LogParserService
from app.models.schemas import LogCreate
from datetime import datetime


def test_log_parser_initialization():
    """Test that the log parser initializes correctly."""
    parser = LogParserService()
    assert parser is not None


def test_normalize_log_basic():
    """Test basic log normalization."""
    parser = LogParserService()

    # Create a test log
    test_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level="INFO",
        message="Test message",
        host="test-host",
        request_id="req_123",
        status_code=200,
        latency_ms=50.0,
        endpoint="/test",
        exception_type=None,
        environment="production"
    )

    # Normalize the log
    # Note: In async testing, we'd need to use await, but for simplicity
    # we'll test the sync parts or use pytest-asyncio
    import asyncio

    async def test_async():
        normalized_logs = await parser.parse_logs([test_log])
        assert len(normalized_logs) == 1
        log = normalized_logs[0]
        assert log.service == "test-service"
        assert log.level.value == "INFO"
        assert log.message == "Test message"

    # Run the async test
    asyncio.run(test_async())


def test_normalize_log_with_missing_fields():
    """Test log normalization with missing fields."""
    parser = LogParserService()

    # Create a test log with some missing fields
    test_log = LogCreate(
        timestamp=datetime.utcnow(),
        service="test-service",
        level="ERROR",
        message="Test error message",
        host=None,  # Missing host
        request_id=None,  # Missing request ID
        status_code=None,  # Missing status code
        latency_ms=None,  # Missing latency
        endpoint=None,  # Missing endpoint
        exception_type="TestException",
        environment="staging"
    )

    import asyncio

    async def test_async():
        normalized_logs = await parser.parse_logs([test_log])
        assert len(normalized_logs) == 1
        log = normalized_logs[0]
        assert log.service == "test-service"
        assert log.level.value == "ERROR"
        assert log.exception_type == "TestException"
        assert log.environment == "staging"
        # Missing fields should remain None
        assert log.host is None
        assert log.request_id is None
        assert log.status_code is None
        assert log.latency_ms is None
        assert log.endpoint is None

    # Run the async test
    asyncio.run(test_async())


if __name__ == "__main__":
    pytest.main([__file__])