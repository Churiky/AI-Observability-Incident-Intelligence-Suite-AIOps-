"""
RAG (Retrieval-Augmented Generation) service for retrieving similar historical incidents.
"""
from typing import List, Optional, Tuple
import numpy as np
import faiss
import pickle
import os
from app.models.database import *
from app.models.schemas import *
from app.services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, db_session):
        self.db = db_session
        self.embedding_service = EmbeddingService()
        self.index = None
        self.incident_ids = []  # Map FAISS indices to incident IDs
        self.index_path = "./ml/artifacts/faiss_index"
        self.metadata_path = "./ml/artifacts/faiss_metadata.pkl"
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        try:
            if os.path.exists(f"{self.index_path}.index") and os.path.exists(self.metadata_path):
                # Load index
                self.index = faiss.read_index(f"{self.index_path}.index")
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.incident_ids = data['incident_ids']
                logger.info(f"Loaded FAISS index with {len(self.incident_ids)} incidents")
            else:
                # Create new index
                self._create_new_index()
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.warning(f"Error loading FAISS index: {e}. Creating new index.")
            self._create_new_index()

    def _create_new_index(self):
        """Create a new FAISS index."""
        # Using Inner Product (IP) for similarity - we'll normalize vectors for cosine similarity
        dimension = 384  # Default for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatIP(dimension)
        self.incident_ids = []

    def add_incident(self, incident_id: int, incident_title: str, incident_description: str = ""):
        """
        Add an incident to the FAISS index for similarity search.
        """
        try:
            # Combine title and description for embedding
            text = f"{incident_title}. {incident_description}".strip()

            # Get embedding
            embedding = self.embedding_service.get_embedding(text)

            # Normalize for cosine similarity using Inner Product
            embedding_normalized = embedding / np.linalg.norm(embedding)
            embedding_normalized = embedding_normalized.reshape(1, -1).astype('float32')

            # Add to index
            self.index.add(embedding_normalized)
            self.incident_ids.append(incident_id)

            # Save index and metadata
            self._save_index()

            logger.debug(f"Added incident {incident_id} to FAISS index")
        except Exception as e:
            logger.error(f"Error adding incident to FAISS index: {e}")

    def search_similar_incidents(self, incident_title: str, incident_description: str = "", k: int = 3) -> List[Tuple[int, float]]:
        """
        Search for similar historical incidents.
        Returns list of (incident_id, similarity_score) tuples.
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []

        try:
            # Combine title and description for embedding
            text = f"{incident_title}. {incident_description}".strip()

            # Get embedding
            embedding = self.embedding_service.get_embedding(text)

            # Normalize for cosine similarity
            embedding_normalized = embedding / np.linalg.norm(embedding)
            embedding_normalized = embedding_normalized.reshape(1, -1).astype('float32')

            # Search
            k = min(k, self.index.ntotal)  # Don't search for more than we have
            scores, indices = self.index.search(embedding_normalized, k)

            # Convert to list of (incident_id, similarity) tuples
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.incident_ids):  # Valid index
                    incident_id = self.incident_ids[idx]
                    # Convert from inner product to cosine similarity (since we normalized)
                    similarity = float(score)  # Already in [-1, 1] range for normalized vectors
                    similarity = max(0.0, min(1.0, (similarity + 1) / 2))  # Convert to [0, 1]
                    results.append((incident_id, similarity))

            logger.debug(f"Found {len(results)} similar incidents for query")
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []

    def get_incident_details(self, incident_id: int) -> Optional[dict]:
        """
        Get detailed information about an incident.
        """
        try:
            incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
            if not incident:
                return None

            return {
                "id": incident.id,
                "title": incident.title,
                "severity": incident.severity,
                "status": incident.status,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "root_cause": incident.root_cause,
                "confidence": incident.confidence,
                "incident_score": incident.incident_score,
                "anomaly_count": len(incident.anomalies)
            }
        except Exception as e:
            logger.error(f"Error getting incident details: {e}")
            return None

    def rebuild_index(self):
        """
        Rebuild the FAISS index from all incidents in the database.
        """
        try:
            logger.info("Rebuilding FAISS index from database incidents")

            # Get all incidents
            incidents = self.db.query(Incident).all()

            # Create new index
            self._create_new_index()

            # Add all incidents
            for incident in incidents:
                description = ""
                # Get AI report if available for richer description
                ai_report = self.db.query(AIReport).filter(AIReport.incident_id == incident.id).first()
                if ai_report:
                    # Extract first 200 chars of report for description
                    description = ai_report.report_markdown[:200] + "..." if len(ai_report.report_markdown) > 200 else ai_report.report_markdown

                self.add_incident(incident.id, incident.title, description)

            logger.info(f"Rebuilt FAISS index with {len(incidents)} incidents")
            return len(incidents)
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {e}")
            return 0

    def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

            # Save index
            faiss.write_index(self.index, f"{self.index_path}.index")

            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'incident_ids': self.incident_ids
                }, f)

            logger.debug("Saved FAISS index and metadata")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")