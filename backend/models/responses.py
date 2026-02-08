from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Citation(BaseModel):
    """Citation model for source attribution."""
    id: int = Field(..., description="Citation number")
    chunk_id: str = Field(..., description="UUID of the source chunk")
    document_id: str = Field(..., description="UUID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    page_number: Optional[int] = Field(None, description="Page number if available")
    content: str = Field(..., description="Snippet of the cited content")
    relevance_score: float = Field(..., description="Relevance score of the chunk")


class ChatMessage(BaseModel):
    """Chat message in response."""
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class Choice(BaseModel):
    """Choice in chat completion response."""
    index: int = Field(0, description="Choice index")
    message: ChatMessage = Field(..., description="Generated message")
    finish_reason: str = Field("stop", description="Reason for completion finish")


class Usage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int = Field(..., description="Number of tokens in prompt")
    completion_tokens: int = Field(..., description="Number of tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")


class ResponseMetadata(BaseModel):
    """Metadata about the response generation."""
    retrieval_time_ms: float = Field(..., description="Time spent on retrieval")
    reranking_time_ms: float = Field(..., description="Time spent on reranking")
    generation_time_ms: float = Field(..., description="Time spent on generation")
    total_time_ms: float = Field(..., description="Total processing time")
    chunks_retrieved: int = Field(..., description="Number of chunks retrieved")
    chunks_reranked: int = Field(..., description="Number of chunks reranked")
    chunks_used: int = Field(..., description="Number of chunks used in final generation")


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str = Field(..., description="Unique completion ID")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used")
    choices: List[Choice] = Field(..., description="List of completion choices")
    usage: Usage = Field(..., description="Token usage statistics")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    version: str = Field(..., description="API version")
