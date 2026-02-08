from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class VectorRepository:
    """Repository for vector search operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_by_embedding(
        self,
        embedding: List[float],
        top_k: int = 20,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search chunks by embedding vector.

        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of chunk dictionaries with similarity scores
        """
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        # Build filter condition
        filter_condition = "TRUE"
        if filters:
            # Simple metadata filtering (can be extended)
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"metadata->>'{key}' = '{value}'")
                elif isinstance(value, (int, float)):
                    filter_parts.append(f"(metadata->>'{key}')::numeric = {value}")

            if filter_parts:
                filter_condition = " AND ".join(filter_parts)

        query = text(f"""
            SELECT
                c.id::text as chunk_id,
                c.document_id::text as document_id,
                c.content,
                c.metadata,
                1 - (c.embedding <=> :embedding::vector) AS similarity
            FROM chunks c
            WHERE {filter_condition}
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        result = await self.session.execute(
            query,
            {"embedding": embedding_str, "top_k": top_k}
        )

        chunks = []
        for row in result:
            chunks.append({
                "id": row.chunk_id,
                "document_id": row.document_id,
                "content": row.content,
                "metadata": row.metadata,
                "score": float(row.similarity)
            })

        return chunks

    async def hybrid_search(
        self,
        embedding: List[float],
        query_text: str,
        top_k: int = 20,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and BM25.

        Args:
            embedding: Query embedding vector
            query_text: Query text for BM25
            top_k: Number of results to return
            vector_weight: Weight for vector similarity
            bm25_weight: Weight for BM25 score

        Returns:
            List of chunk dictionaries with combined scores
        """
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        query = text("""
            WITH vector_search AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.content,
                    c.metadata,
                    1 - (c.embedding <=> :embedding::vector) AS score
                FROM chunks c
                ORDER BY c.embedding <=> :embedding::vector
                LIMIT :top_k_mult
            ),
            bm25_search AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.content,
                    c.metadata,
                    ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', :query_text)) AS score
                FROM chunks c
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', :query_text)
                ORDER BY score DESC
                LIMIT :top_k_mult
            )
            SELECT
                COALESCE(v.id, b.id)::text AS chunk_id,
                COALESCE(v.document_id, b.document_id)::text AS document_id,
                COALESCE(v.content, b.content) AS content,
                COALESCE(v.metadata, b.metadata) AS metadata,
                (COALESCE(v.score, 0) * :vector_weight + COALESCE(b.score, 0) * :bm25_weight) AS combined_score,
                COALESCE(v.score, 0) AS vector_score,
                COALESCE(b.score, 0) AS bm25_score
            FROM vector_search v
            FULL OUTER JOIN bm25_search b ON v.id = b.id
            ORDER BY combined_score DESC
            LIMIT :top_k
        """)

        result = await self.session.execute(
            query,
            {
                "embedding": embedding_str,
                "query_text": query_text,
                "top_k": top_k,
                "top_k_mult": top_k * 2,
                "vector_weight": vector_weight,
                "bm25_weight": bm25_weight
            }
        )

        chunks = []
        for row in result:
            chunks.append({
                "id": row.chunk_id,
                "document_id": row.document_id,
                "content": row.content,
                "metadata": row.metadata,
                "score": float(row.combined_score),
                "vector_score": float(row.vector_score),
                "bm25_score": float(row.bm25_score)
            })

        return chunks

    async def get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        """
        Get a specific chunk by ID.

        Args:
            chunk_id: UUID of the chunk

        Returns:
            Chunk dictionary
        """
        query = text("""
            SELECT
                c.id::text as chunk_id,
                c.document_id::text as document_id,
                c.content,
                c.metadata,
                d.filename as document_name
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.id = :chunk_id
        """)

        result = await self.session.execute(query, {"chunk_id": chunk_id})
        row = result.first()

        if not row:
            return None

        return {
            "id": row.chunk_id,
            "document_id": row.document_id,
            "content": row.content,
            "metadata": row.metadata,
            "document_name": row.document_name
        }
