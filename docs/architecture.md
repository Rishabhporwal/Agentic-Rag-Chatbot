# Architecture Deep Dive

## System Architecture

The Agentic RAG system follows a layered microservices architecture with clear separation of concerns.

### Layers

1. **Presentation Layer**: OpenWebUI provides the user interface
2. **API Layer**: FastAPI exposes REST endpoints
3. **Orchestration Layer**: CrewAI manages agent workflows
4. **Service Layer**: Core business logic (retrieval, memory, LLM)
5. **Data Layer**: PostgreSQL + PGVector for storage

## Component Details

### Document Indexer

**Purpose**: Transform raw documents into searchable embeddings

**Key Decisions**:
- Chunking: 512 tokens with 50 token overlap balances context and granularity
- Semantic boundaries: Split on sentences to maintain coherence
- Batch processing: Process 50 chunks at a time for efficiency
- Embedding model: nomic-embed-text (768-dim, 8192 context, open-source)

**Process**:
1. Docling parses documents and extracts structure
2. Chunker splits content respecting semantic boundaries
3. Metadata extractor enriches chunks with document info
4. Batch processor generates embeddings via Ollama
5. Vector store saves to PostgreSQL with PGVector

### Backend API

**Purpose**: Orchestrate intelligent RAG pipeline

**Key Decisions**:
- Framework: FastAPI for async support and auto-documentation
- Agent framework: CrewAI for multi-agent orchestration
- Database: PostgreSQL + PGVector for hybrid search
- LLM: Llama 3.1 8B (quantized) for performance

**Architecture**:
- **API Layer**: OpenAI-compatible endpoints
- **Agent Layer**: Four specialized CrewAI agents
- **Service Layer**: Reusable business logic
- **Repository Layer**: Database access patterns

### Hybrid Retrieval

**Purpose**: Find most relevant chunks using multiple signals

**Strategy**:
1. **Vector Search**: Cosine similarity on embeddings (60% weight)
2. **BM25 Search**: Keyword matching via PostgreSQL FTS (40% weight)
3. **Fusion**: Reciprocal Rank Fusion combines results
4. **Filtering**: Optional metadata-based pre-filtering

**Performance**:
- IVFFlat index for approximate nearest neighbor search
- Full-text search index for BM25
- Combined query executes in < 100ms for 100K chunks

### Agent System

**Purpose**: Multi-step reasoning for better answers

**Design**:
- **Sequential Process**: Agents execute in order
- **Tool-Based**: Each agent has specialized tools
- **Observable**: Phoenix traces every agent execution

**Flow**:
```
Query → Retriever (hybrid search) → 20 chunks
      → Reranker (LLM scoring) → 5 chunks
      → Synthesizer (answer + citations) → response
      → Guardrails (validation) → approved response
```

### Conversation Memory

**Purpose**: Maintain context across multiple turns

**Design**:
- **Storage**: PostgreSQL for persistence
- **Window**: Last 10 messages or 4096 tokens
- **Summarization**: Older messages compressed
- **Lifecycle**: Auto-cleanup after inactivity

### Observability

**Purpose**: Debug, monitor, and improve the system

**Integration**:
- **Phoenix**: Prompt management, tracing, metrics
- **Logging**: Structured logs at all levels
- **Metrics**: Timing, counts, success rates
- **Health Checks**: Dependency status monitoring

## Design Decisions

### Why Hybrid Search?

Vector search alone misses exact keyword matches. BM25 alone misses semantic similarity. Hybrid search gets best of both.

### Why Two-Stage Reranking?

Neural reranking is fast but less accurate. LLM reranking is accurate but slow. Two-stage combines speed and accuracy.

### Why Sequential Agents?

Sequential process ensures quality gates at each step. Retriever must finish before reranker can work on results.

### Why PostgreSQL Over Dedicated Vector DB?

PostgreSQL + PGVector provides:
- ACID compliance
- Hybrid search (vectors + FTS)
- Mature ecosystem
- Lower operational complexity

For systems < 10M vectors, PostgreSQL performs excellently.

## Scalability

### Current Limits

- Documents: ~100K
- Chunks: ~1M
- Concurrent Users: ~100
- Response Time: 2-5 seconds

### Scaling Path

1. **Backend**: Horizontal scaling with load balancer
2. **Database**: Managed PostgreSQL with read replicas
3. **Ollama**: GPU instances with model caching
4. **Phoenix**: Separate observability cluster

## Security

### Current Implementation

- Environment-based secrets
- Input validation (Pydantic)
- Prepared statements (SQL injection prevention)
- Content filtering (Guardrails agent)

### Production Additions

- API authentication (JWT)
- Rate limiting (per user/IP)
- Audit logging
- Encryption at rest
- Network segmentation
