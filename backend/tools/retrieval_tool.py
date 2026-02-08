from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from services.retrieval_service import RetrievalService
import asyncio
import json


class RetrievalInput(BaseModel):
    """Input schema for retrieval tool."""
    query: str = Field(..., description="Query text to search for")
    top_k: int = Field(20, description="Number of chunks to retrieve")


class RetrievalTool(BaseTool):
    name: str = "retrieval_tool"
    description: str = "Retrieves relevant document chunks using hybrid search (vector + BM25)"
    args_schema: Type[BaseModel] = RetrievalInput

    def _run(self, query: str, top_k: int = 20) -> str:
        """
        Run retrieval synchronously (CrewAI requires sync).

        Args:
            query: Query text
            top_k: Number of chunks to retrieve

        Returns:
            JSON string with retrieval results
        """
        # Run async retrieval in sync context
        retrieval_service = RetrievalService()
        result = asyncio.run(retrieval_service.retrieve(query=query, top_k=top_k))

        # Format results for agent consumption
        output = {
            "success": True,
            "chunks_count": len(result["chunks"]),
            "chunks": [
                {
                    "id": chunk["id"],
                    "content": chunk["content"][:300] + "..." if len(chunk["content"]) > 300 else chunk["content"],
                    "score": chunk["score"],
                    "document": chunk["metadata"].get("document_filename", "Unknown")
                }
                for chunk in result["chunks"]
            ],
            "retrieval_time_ms": result["retrieval_time_ms"]
        }

        return json.dumps(output, indent=2)
