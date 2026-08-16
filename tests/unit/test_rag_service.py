"""
Unit tests for the RAG service.
"""
import pytest
import numpy as np
import faiss
from unittest.mock import Mock, MagicMock, patch
from app.services.rag_service import RAGService
from app.models.database import *
from app.models.schemas import *
from app.services.embedding_service import EmbeddingService


def test_rag_service_initialization():
    """Test that the RAG service initializes correctly."""
    mock_db = Mock()
    rag_service = RAGService(mock_db)
    assert rag_service is not None
    assert rag_service.db == mock_db
    assert rag_service.embedding_service is not None


def test_create_new_index():
    """Test that a new FAISS index is created correctly."""
    mock_db = Mock()
    rag_service = RAGService(mock_db)

    # Check that index was created
    assert rag_service.index is not None
    assert isinstance(rag_service.index, faiss.IndexFlatIP)
    assert rag_service.index.d == 384  # Default dimension
    assert rag_service.incident_ids == []


@patch('app.services.rag_service.EmbeddingService')
def test_add_incident(mock_embedding_service):
    """Test adding an incident to the FAISS index."""
    # Setup mock
    mock_embedding_instance = Mock()
    mock_embedding_instance.get_embedding.return_value = np.array([0.1, 0.2, 0.3] + [0.0] * 381)  # 384 dim
    mock_embedding_service.return_value = mock_embedding_instance

    mock_db = Mock()
    rag_service = RAGService(mock_db)
    # Replace the embedding service with our mock
    rag_service.embedding_service = mock_embedding_instance

    # Add an incident
    rag_service.add_incident(1, "Test Incident", "Test description")

    # Check that the index now has one vector
    assert rag_service.index.ntotal == 1
    assert len(rag_service.incident_ids) == 1
    assert rag_service.incident_ids[0] == 1


def test_search_similar_incidents_empty_index():
    """Test searching when index is empty."""
    mock_db = Mock()
    rag_service = RAGService(mock_db)

    # Search empty index
    results = rag_service.search_similar_incidents("Test query")
    assert results == []


def test_get_incident_details():
    """Test getting incident details."""
    mock_db = Mock()

    # Mock incident
    mock_incident = Mock(spec=Incident)
    mock_incident.id = 1
    mock_incident.title = "Test Incident"
    mock_incident.severity = "HIGH"
    mock_incident.status = "ACTIVE"
    mock_incident.created_at = datetime.utcnow()
    mock_incident.resolved_at = None
    mock_incident.root_cause = "Test cause"
    mock_incident.confidence = 0.85
    mock_incident.incident_score = 0.75
    mock_incident.anomalies = [Mock(), Mock()]  # Two anomalies

    # Setup database query to return our mock incident
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_incident
    mock_db.query.return_value = mock_query

    rag_service = RAGService(mock_db)

    # Get incident details
    details = rag_service.get_incident_details(1)

    assert details is not None
    assert details['id'] == 1
    assert details['title'] == "Test Incident"
    assert details['severity'] == "HIGH"
    assert details['status'] == "ACTIVE"
    assert details['anomaly_count'] == 2


def test_get_incident_details_not_found():
    """Test getting incident details when incident doesn't exist."""
    mock_db = Mock()

    # Setup database query to return None
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query

    rag_service = RAGService(mock_db)

    # Get incident details
    details = rag_service.get_incident_details(999)

    assert details is None


if __name__ == "__main__":
    pytest.main([__file__])