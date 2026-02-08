import logging
import requests
from typing import List


logger = logging.getLogger("backend.embedding_service")


class EmbeddingService:
    """Service for generating embeddings using Ollama."""

    def __init__(self, base_url: str, model: str):
        """
        Initialize the embedding service.

        Args:
            base_url: Base URL for Ollama API
            model: Name of the embedding model
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.embed_url = f"{self.base_url}/api/embeddings"
        logger.info(f"EmbeddingService initialized (model={model})")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        payload = {
            "model": self.model,
            "prompt": text
        }

        try:
            response = requests.post(
                self.embed_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            embedding = result.get("embedding")

            if not embedding:
                raise RuntimeError("No embedding in response")

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
