from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import re


class CitationInput(BaseModel):
    """Input schema for citation tool."""
    response_text: str = Field(..., description="Generated response text with citation markers")
    chunks_json: str = Field(..., description="JSON string of chunks used")


class CitationTool(BaseTool):
    name: str = "citation_tool"
    description: str = "Extracts and validates citations from generated response"
    args_schema: Type[BaseModel] = CitationInput

    def _run(self, response_text: str, chunks_json: str) -> str:
        """
        Extract citations from response.

        Args:
            response_text: Generated response with citation markers
            chunks_json: JSON string of available chunks

        Returns:
            JSON string with citation data
        """
        try:
            chunks = json.loads(chunks_json)

            # Find all citation markers [1], [2], etc.
            citation_pattern = r'\[(\d+)\]'
            cited_numbers = set(map(int, re.findall(citation_pattern, response_text)))

            # Build citation list
            citations = []
            for i, chunk in enumerate(chunks):
                citation_num = i + 1
                if citation_num in cited_numbers:
                    citations.append({
                        "id": citation_num,
                        "chunk_id": chunk["id"],
                        "document_id": chunk.get("document_id", ""),
                        "document_name": chunk.get("document", "Unknown"),
                        "content": chunk["content"][:200] + "...",
                        "relevance_score": chunk.get("score", 0.0)
                    })

            output = {
                "success": True,
                "citations_count": len(citations),
                "citations": citations
            }

            return json.dumps(output, indent=2)

        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
