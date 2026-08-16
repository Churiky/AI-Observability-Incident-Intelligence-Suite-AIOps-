"""
Embedding service for generating vector representations of text.
"""
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import os
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Fallback to a simple approach or raise
            raise

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings for a list of texts.
        Returns numpy array of shape (len(texts), embedding_dim).
        """
        if not texts:
            return np.array([])

        if self.model is None:
            self._load_model()

        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return zero vectors as fallback
            return np.zeros((len(texts), 384))  # Default dimension for all-MiniLM-L6-v2

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a single text.
        Returns numpy array of shape (embedding_dim,).
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0] if len(embeddings) > 0 else np.zeros(384)

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        Returns similarity score between 0 and 1.
        """
        if not text1 or not text2:
            return 0.0

        try:
            emb1 = self.get_embedding(text1)
            emb2 = self.get_embedding(text2)

            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, (similarity + 1) / 2))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0