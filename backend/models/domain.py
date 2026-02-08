from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChunkData(BaseModel):
    """Represents a chunk retrieved from the vector store."""
    id: str = Field(..., description="Chunk UUID")
    document_id: str = Field(..., description="Document UUID")
    content: str = Field(..., description="Chunk content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    score: float = Field(..., description="Relevance score")


class RetrievalResult(BaseModel):
    """Result from retrieval operation."""
    chunks: List[ChunkData] = Field(..., description="Retrieved chunks")
    query: str = Field(..., description="Original query")
    retrieval_time_ms: float = Field(..., description="Time taken for retrieval")
    total_retrieved: int = Field(..., description="Total number of chunks retrieved")


class RerankingResult(BaseModel):
    """Result from reranking operation."""
    chunks: List[ChunkData] = Field(..., description="Reranked chunks")
    reranking_time_ms: float = Field(..., description="Time taken for reranking")


class GenerationResult(BaseModel):
    """Result from generation operation."""
    content: str = Field(..., description="Generated content")
    citations: List[int] = Field(default_factory=list, description="Citation indices used")
    generation_time_ms: float = Field(..., description="Time taken for generation")
    token_count: int = Field(..., description="Number of tokens generated")
