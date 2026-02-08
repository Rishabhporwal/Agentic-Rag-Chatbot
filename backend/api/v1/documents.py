from fastapi import APIRouter, Query
from typing import List, Dict, Any
from sqlalchemy import text
from database.connection import SessionLocal


router = APIRouter()


@router.get("/documents")
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    List indexed documents.

    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip

    Returns:
        List of documents with metadata
    """
    async with SessionLocal() as session:
        # Get documents
        query = text("""
            SELECT
                id::text,
                filename,
                file_type,
                title,
                author,
                indexed_at,
                (SELECT COUNT(*) FROM chunks WHERE document_id = documents.id) as chunk_count
            FROM documents
            ORDER BY indexed_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(query, {"limit": limit, "offset": offset})
        rows = result.fetchall()

        documents = [
            {
                "id": row[0],
                "filename": row[1],
                "file_type": row[2],
                "title": row[3],
                "author": row[4],
                "indexed_at": row[5].isoformat() if row[5] else None,
                "chunk_count": row[6]
            }
            for row in rows
        ]

        # Get total count
        count_query = text("SELECT COUNT(*) FROM documents")
        count_result = await session.execute(count_query)
        total = count_result.scalar()

        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset
        }
