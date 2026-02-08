# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Chat Completion

Create a chat completion with RAG.

**Endpoint**: `POST /v1/chat/completions`

**Request Body**:
```json
{
  "model": "agentic-rag",
  "messages": [
    {"role": "user", "content": "What is RAG?"}
  ],
  "session_id": "optional-session-id",
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2048,
  "retrieval_params": {
    "top_k": 20,
    "rerank_top_k": 5,
    "filters": {
      "document_type": "pdf"
    }
  }
}
```

**Response**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "agentic-rag",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "RAG stands for Retrieval-Augmented Generation [1][2]..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  },
  "citations": [
    {
      "id": 1,
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "rag_paper.pdf",
      "page_number": 3,
      "content": "Retrieval-Augmented Generation...",
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "retrieval_time_ms": 120,
    "reranking_time_ms": 80,
    "generation_time_ms": 450,
    "total_time_ms": 650,
    "chunks_retrieved": 20,
    "chunks_reranked": 5,
    "chunks_used": 2
  }
}
```

### Get Conversation

Retrieve conversation history.

**Endpoint**: `GET /v1/conversations/{session_id}`

**Response**:
```json
{
  "session_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "What is RAG?"
    },
    {
      "role": "assistant",
      "content": "RAG is..."
    }
  ],
  "message_count": 2
}
```

### Delete Conversation

Delete conversation history.

**Endpoint**: `DELETE /v1/conversations/{session_id}`

**Response**:
```json
{
  "status": "deleted",
  "session_id": "abc123"
}
```

### List Documents

List indexed documents.

**Endpoint**: `GET /v1/documents?limit=50&offset=0`

**Response**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "document.pdf",
      "file_type": "pdf",
      "title": "Document Title",
      "author": "Author Name",
      "indexed_at": "2024-01-15T10:00:00Z",
      "chunk_count": 42
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### Health Check

Check service health.

**Endpoint**: `GET /v1/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "services": {
    "database": "healthy",
    "ollama": "healthy",
    "phoenix": "healthy"
  },
  "version": "1.0.0"
}
```

## Status Codes

- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Internal server error

## Rate Limits

Development: No limits
Production: Implement at API Gateway level
