from crewai_tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from services.llm_service import LLMService
from config.settings import settings
import json


class RerankingInput(BaseModel):
    """Input schema for reranking tool."""
    query: str = Field(..., description="Original query text")
    chunks_json: str = Field(..., description="JSON string of chunks to rerank")
    top_k: int = Field(5, description="Number of top chunks to return")


class RerankingTool(BaseTool):
    name: str = "reranking_tool"
    description: str = "Reranks retrieved chunks by relevance to the query"
    args_schema: Type[BaseModel] = RerankingInput

    def _run(self, query: str, chunks_json: str, top_k: int = 5) -> str:
        """
        Rerank chunks by relevance.

        Args:
            query: Original query
            chunks_json: JSON string of chunks
            top_k: Number of top chunks to return

        Returns:
            JSON string with reranked results
        """
        try:
            chunks = json.loads(chunks_json)

            # Use LLM-based reranking for top candidates
            llm_service = LLMService(
                base_url=settings.ollama_base_url,
                model=settings.llm_model
            )

            reranked = []
            for chunk in chunks[:top_k * 2]:  # Score top candidates
                relevance_score = llm_service.score_relevance(query, chunk["content"])
                chunk["rerank_score"] = relevance_score
                reranked.append(chunk)

            # Sort by rerank score and take top_k
            reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            final_chunks = reranked[:top_k]

            output = {
                "success": True,
                "reranked_count": len(final_chunks),
                "chunks": final_chunks
            }

            return json.dumps(output, indent=2)

        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
