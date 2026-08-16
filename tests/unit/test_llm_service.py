"""
Unit tests for the LLM service.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.llm_service import LLMService
from app.models.database import *
from app.models.schemas import *
from app.core.config import Settings


def test_llm_service_initialization():
    """Test that the LLM service initializes correctly."""
    llm_service = LLMService()
    assert llm_service is not None
    assert llm_service.ollama_base_url is not None
    assert llm_service.ollama_model is not None
    assert llm_service.session is not None


@patch('app.services.llm_service.requests.Session')
def test_llm_service_initialization_with_mock_session(mock_session_class):
    """Test LLM service initialization with mocked session."""
    mock_session_instance = Mock()
    mock_session_class.return_value = mock_session_instance

    llm_service = LLMService()
    assert llm_service.session == mock_session_instance


def test_gather_incident_evidence():
    """Test gathering incident evidence."""
    llm_service = LLMService()

    evidence = llm_service._gather_incident_evidence(123)

    assert isinstance(evidence, dict)
    assert evidence['incident_id'] == 123
    assert 'timestamp' in evidence
    assert 'service' in evidence
    assert 'anomalies' in evidence
    assert 'metrics' in evidence
    assert isinstance(evidence['anomalies'], list)
    assert isinstance(evidence['metrics'], dict)


def test_prepare_similar_incidents_context():
    """Test preparing similar incidents context."""
    llm_service = LLMService()

    # Mock RAG service
    mock_rag_service = Mock()
    mock_rag_service.get_incident_details.side_effect = [
        {
            'id': 1,
            'title': 'Test Incident 1',
            'severity': 'HIGH',
            'root_cause': 'Database issue',
            'resolved_at': '2026-08-16T11:00:00'
        },
        {
            'id': 2,
            'title': 'Test Incident 2',
            'severity': 'MEDIUM',
            'root_cause': 'Not specified',  # Should be filtered out
            'resolved_at': None
        }
    ]

    similar_incidents = [(1, 0.95), (2, 0.80)]
    context = llm_service._prepare_similar_incidents_context(similar_incidents, mock_rag_service)

    assert len(context) == 2  # Both incidents should be included
    assert context[0]['incident_id'] == 1
    assert context[0]['similarity_score'] == 0.95
    assert context[0]['title'] == 'Test Incident 1'
    assert context[0]['root_cause'] == 'Database issue'

    assert context[1]['incident_id'] == 2
    assert context[1]['similarity_score'] == 0.80
    assert context[1]['title'] == 'Test Incident 2'
    assert context[1]['root_cause'] == 'Not specified'


def test_format_evidence():
    """Test evidence formatting."""
    llm_service = LLMService()

    evidence = {
        'service': 'test-service',
        'timestamp': '2026-08-16T10:23:41',
        'anomalies': [
            {
                'description': 'Test anomaly',
                'confidence': 0.95
            }
        ],
        'metrics': {
            'error_rate': 0.15,
            'latency': 1.5
        }
    }

    formatted = llm_service._format_evidence(evidence)

    assert 'test-service' in formatted
    assert '2026-08-16T10:23:41' in formatted
    assert 'Test anomaly' in formatted
    assert '0.95' in formatted
    assert 'error_rate' in formatted
    assert '0.15' in formatted
    assert 'latency' in formatted
    assert '1.5' in formatted


def test_format_similar_incidents():
    """Test similar incidents formatting."""
    llm_service = LLMService()

    similar_incidents = [
        {
            'incident_id': 1,
            'similarity_score': 0.95,
            'title': 'Test Incident 1',
            'severity': 'HIGH',
            'root_cause': 'Database issue',
            'resolved_at': '2026-08-16T11:00:00'
        },
        {
            'incident_id': 2,
            'similarity_score': 0.80,
            'title': 'Test Incident 2',
            'severity': 'MEDIUM',
            'root_cause': 'Not specified',
            'resolved_at': None
        }
    ]

    formatted = llm_service._format_similar_incidents(similar_incidents)

    assert 'Incident 1' in formatted
    assert 'Test Incident 1' in formatted
    assert '0.95' in formatted
    assert 'HIGH' in formatted
    assert 'Database issue' in formatted

    assert 'Incident 2' in formatted
    assert 'Test Incident 2' in formatted
    assert '0.80' in formatted
    assert 'MEDIUM' in formatted
    assert 'Not specified' in formatted


def test_construct_evidence_based_prompt():
    """Test prompt construction."""
    llm_service = LLMService()

    incident_details = {
        'id': 123,
        'title': 'Test Incident',
        'severity': 'HIGH',
        'status': 'ACTIVE',
        'created_at': '2026-08-16T10:23:41'
    }

    evidence = {
        'service': 'payment-service',
        'timestamp': '2026-08-16T10:23:41',
        'anomalies': [
            {
                'description': 'Database timeout increased 340%',
                'confidence': 0.95
            }
        ],
        'metrics': {
            'error_rate_increase': 0.18
        }
    }

    similar_incidents_context = [
        {
            'incident_id': 456,
            'similarity_score': 0.85,
            'title': 'Similar Incident',
            'severity': 'HIGH',
            'root_cause': 'DB connection pool exhaustion',
            'resolved_at': '2026-07-15T09:30:00'
        }
    ]

    prompt = llm_service._construct_evidence_based_prompt(
        incident_details, evidence, similar_incidents_context
    )

    assert 'Test Incident' in prompt
    assert 'payment-service' in prompt
    assert 'Database timeout increased 340%' in prompt
    assert '0.95' in prompt
    assert '0.18' in prompt
    assert 'Similar Incident' in prompt
    assert 'DB connection pool exhaustion' in prompt
    assert 'INSTRUCTIONS:' in prompt
    assert 'RULES:' in prompt
    assert 'REPORT FORMAT:' in prompt
    assert 'Incident Summary:' in prompt
    assert 'Impact:' in prompt
    assert 'Probable Cause:' in prompt
    assert 'Recommended Investigation:' in prompt
    assert 'Confidence:' in prompt


def test_post_process_report():
    """Test report post-processing."""
    llm_service = LLMService()

    # Test with properly formatted report
    report = """Incident Summary: Test incident occurred.
Impact: Service degradation observed.
Probable Cause: Database connection issue.
Recommended Investigation:
1. Check database connections
2. Review logs
Confidence: Probable"""

    processed = llm_service._post_process_report(report, 123)
    assert processed.strip() == report.strip()

    # Test with missing sections (should return as-is but log warning)
    incomplete_report = "Incident Summary: Test"
    processed = llm_service._post_process_report(incomplete_report, 123)
    assert processed == incomplete_report.strip()


def test_get_fallback_report():
    """Test fallback report generation."""
    llm_service = LLMService()

    fallback = llm_service._get_fallback_report(456)

    assert '456' in fallback
    assert 'Incident Summary:' in fallback
    assert 'Impact:' in fallback
    assert 'Probable Cause:' in fallback
    assert 'Recommended Investigation:' in fallback
    assert 'Confidence:' in fallback
    assert 'Unknown' in fallback  # Should default to Unknown


if __name__ == "__main__":
    pytest.main([__file__])