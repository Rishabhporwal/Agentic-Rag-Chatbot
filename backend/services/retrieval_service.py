import logging
from typing import List, Dict, Any
from config.settings import settings
from services.embedding_service import EmbeddingService
from database.connection import SessionLocal
from database.repositories.vector_repo import VectorRepository
import time


logger = logging.getLogger("backend.retrieval_service")


class RetrievalService:
    """Service for hybrid retrieval operations."""

    def __init__(self):
        """Initialize the retrieval service."""
        self.embedding_service = EmbeddingService(
            base_url=settings.ollama_base_url,
            model=settings.embedding_model
        )
        logger.info("RetrievalService initialized")

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks using hybrid search.

        Args:
            query: Query text
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters

        Returns:
            Dictionary with chunks and metadata
        """
        start_time = time.time()
        top_k = top_k or settings.retrieval_top_k

        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)

            # Perform hybrid search
            async with SessionLocal() as session:
                vector_repo = VectorRepository(session)
                chunks = await vector_repo.hybrid_search(
                    embedding=query_embedding,
                    query_text=query,
                    top_k=top_k,
                    vector_weight=settings.vector_weight,
                    bm25_weight=settings.bm25_weight
                )

            retrieval_time = (time.time() - start_time) * 1000

            logger.info(f"Retrieved {len(chunks)} chunks in {retrieval_time:.2f}ms")

            return {
                "chunks": chunks,
                "query": query,
                "retrieval_time_ms": retrieval_time,
                "total_retrieved": len(chunks)
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise RuntimeError(f"Failed to retrieve chunks: {str(e)}")

    async def get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        """
        Get a specific chunk by ID.

        Args:
            chunk_id: UUID of the chunk

        Returns:
            Chunk dictionary
        """
        async with SessionLocal() as session:
            vector_repo = VectorRepository(session)
            return await vector_repo.get_chunk_by_id(chunk_id)
