from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class RetrievalParams(BaseModel):
    """Parameters for retrieval configuration."""
    top_k: Optional[int] = Field(20, description="Number of chunks to retrieve")
    rerank_top_k: Optional[int] = Field(5, description="Number of chunks after reranking")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata filters")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(default="agentic-rag", description="Model identifier")
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    session_id: Optional[str] = Field(None, description="Session ID for conversation memory")
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(2048, ge=1, description="Maximum tokens to generate")
    retrieval_params: Optional[RetrievalParams] = Field(
        default_factory=RetrievalParams,
        description="Parameters for retrieval"
    )
