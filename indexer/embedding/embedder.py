import logging
import requests
from typing import List, Dict, Any
import time


logger = logging.getLogger("indexer.embedder")


class Embedder:
    """Generates embeddings using Ollama embedding models."""

    def __init__(self, base_url: str, model: str = "nomic-embed-text"):
        """
        Initialize the embedder.

        Args:
            base_url: Base URL for Ollama API
            model: Name of the embedding model
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.embed_url = f"{self.base_url}/api/embeddings"
        logger.info(f"Embedder initialized (model={model}, url={base_url})")

        # Verify connection
        self._verify_connection()

    def _verify_connection(self):
        """Verify connection to Ollama API."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Successfully connected to Ollama API")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API: {str(e)}")
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")

    def embed_text(self, text: str, retry_count: int = 3) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed
            retry_count: Number of retries on failure

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If text is empty
            RuntimeError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        payload = {
            "model": self.model,
            "prompt": text
        }

        for attempt in range(retry_count):
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

                logger.debug(f"Generated embedding of dimension {len(embedding)}")
                return embedding

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise RuntimeError("Embedding request timed out")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Failed to generate embedding: {str(e)}")

        raise RuntimeError("Failed to generate embedding after all retries")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = []

        for idx, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)

                if (idx + 1) % 10 == 0:
                    logger.info(f"Progress: {idx + 1}/{len(texts)} embeddings generated")

            except Exception as e:
                logger.error(f"Failed to embed text {idx}: {str(e)}")
                # Append None for failed embeddings
                embeddings.append(None)

        successful = sum(1 for e in embeddings if e is not None)
        logger.info(f"Successfully generated {successful}/{len(texts)} embeddings")

        return embeddings
