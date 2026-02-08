# Agentic RAG System

A **production-grade, open-source Agentic RAG (Retrieval-Augmented Generation) system** with multi-agent orchestration, comprehensive observability, and full citation support.

## 🎯 Overview

This system combines cutting-edge RAG techniques with intelligent agent orchestration to deliver accurate, cited responses from your document knowledge base. It features:

- **Multi-Agent Architecture**: Four specialized CrewAI agents (Retriever, Reranker, Synthesizer, Guardrails)
- **Hybrid Retrieval**: Combines vector search (semantic) with BM25 (keyword) for optimal results
- **Full Observability**: Arize Phoenix integration for prompt management and tracing
- **Citation Tracking**: Every response includes traceable citations to source documents
- **Conversation Memory**: Session-aware context management with sliding windows
- **Production-Ready**: Docker Compose deployment, health checks, error handling

### Core Components

1. **Document Indexer**: Ingests documents using Docling, chunks them semantically, generates embeddings via Ollama, and stores in PostgreSQL + PGVector
2. **Backend API**: FastAPI service orchestrating CrewAI agents with OpenAI-compatible endpoints
3. **RAG Evaluator**: Evaluates system quality using RAGAs metrics (context precision, recall, faithfulness, answer relevance)
4. **OpenWebUI**: User-friendly chat interface
5. **Ollama**: Hosts open-source models (nomic-embed-text, llama3.1:8b)
6. **Arize Phoenix**: Observability and prompt management
7. **PostgreSQL + PGVector**: Vector database with hybrid search support

## ✨ Features

- **Contextual Agentic RAG**: Multi-step reasoning with context refinement before generation
- **Hybrid Retrieval**: Vector similarity + BM25 keyword search with Reciprocal Rank Fusion
- **Two-Stage Reranking**: Neural reranking followed by LLM-based relevance scoring
- **Citation Tracking**: Inline citations [1], [2] with full source metadata
- **Conversation Memory**: Persistent, queryable conversation history
- **Production-Grade**: Health checks, error handling, connection pooling, logging
- **Comprehensive Evaluation**: RAGAs metrics for continuous quality monitoring

## 📋 Prerequisites

- Docker & Docker Compose
- 16GB+ RAM (8GB for Ollama, 8GB for services)
- 50GB+ disk space
- (Optional) NVIDIA GPU for faster inference

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd agentic-rag

# Copy environment file
cp .env.example .env

# Edit .env and set a secure POSTGRES_PASSWORD
nano .env
```

### 2. Run Setup Script

```bash
# Make script executable and run
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This script will:
- Start PostgreSQL, Ollama, and Phoenix
- Initialize the database schema
- Pull Ollama models (nomic-embed-text, llama3.1:8b)
- Build the backend Docker image
- Start all services

**Alternative manual setup:**

```bash
# Using Makefile
make setup
make up
make pull-models
```

### 3. Index Documents

Place your documents in `./data/documents/` directory:

```bash
# Add your PDF, DOCX, TXT, or MD files
cp /path/to/your/documents/*.pdf ./data/documents/

# Run indexer
docker-compose run --rm indexer python main.py --input /data/documents
```

### 4. Access the System

- **OpenWebUI**: http://localhost:3000 (Chat interface)
- **Backend API**: http://localhost:8000 (API documentation at /docs)
- **Phoenix UI**: http://localhost:6006 (Observability dashboard)

## 📚 Usage

### Indexing Documents

```bash
# Index documents from a directory
docker-compose run --rm indexer python main.py --input /path/to/documents

# With custom batch size
docker-compose run --rm indexer python main.py --input /path/to/documents --batch-size 100

# Check indexing logs
docker-compose logs indexer
```

### Chatting via OpenWebUI

1. Navigate to http://localhost:3000
2. Create an account or sign in
3. Start a new conversation
4. Ask questions about your indexed documents
5. Receive responses with inline citations [1], [2]

### Using the API Directly

```bash
# Chat completion request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agentic-rag",
    "messages": [{"role": "user", "content": "What is RAG?"}],
    "session_id": "my-session-123"
  }'

# Get conversation history
curl http://localhost:8000/v1/conversations/my-session-123

# List documents
curl http://localhost:8000/v1/documents

# Health check
curl http://localhost:8000/v1/health
```

### Evaluating the System

```bash
# Run evaluation with default dataset
docker-compose run --rm evaluator python main.py

# With custom dataset
docker-compose run --rm evaluator python main.py --dataset /path/to/qa_pairs.json

# View reports
ls data/reports/
```

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=agentic_rag
POSTGRES_USER=rag_user

# Ollama Models
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=llama3.1:8b-instruct-q4_K_M

# Retrieval
RETRIEVAL_TOP_K=20
RERANK_TOP_K=5
FINAL_TOP_K=3

# Memory
MAX_MEMORY_MESSAGES=10
MAX_MEMORY_TOKENS=4096
```

### Chunking Strategy

Configured in `indexer/config/settings.py`:

- **Chunk Size**: 512 tokens (balances context vs. granularity)
- **Overlap**: 50 tokens (maintains continuity)
- **Semantic Boundaries**: Splits on sentence boundaries

### Retrieval Strategy

Configured in `backend/config/settings.py`:

- **Hybrid Search**: 60% vector similarity, 40% BM25
- **Top-K Pipeline**: Retrieve 20 → Rerank to 5 → Use top 3
- **Fusion**: Reciprocal Rank Fusion (RRF)

## 🏃 Common Commands

```bash
# Start all services
make up

# Stop all services
make down

# Restart services
make restart

# View logs
make logs
make logs-backend
make logs-postgres

# Index documents
make index

# Run evaluation
make evaluate

# Clean up (remove containers and volumes)
make clean

# Check service status
make status
```

## 🔍 Agent Design

### 1. Retriever Agent

**Role**: RAG Retrieval Specialist

**Responsibilities**:
- Performs hybrid search (vector + BM25)
- Applies metadata filtering
- Returns top 20 candidate chunks with scores

**Tools**: RetrievalTool

### 2. Reranker Agent

**Role**: Relevance Ranking Specialist

**Responsibilities**:
- Reranks chunks using neural and LLM-based scoring
- Removes redundant information
- Returns top 5 most relevant chunks

**Tools**: RerankingTool

### 3. Synthesizer Agent

**Role**: Answer Synthesis Expert

**Responsibilities**:
- Retrieves conversation memory
- Generates comprehensive answers with inline citations
- Ensures factual grounding in provided context

**Tools**: MemoryTool, CitationTool

### 4. Guardrails Agent

**Role**: Quality Assurance and Safety Specialist

**Responsibilities**:
- Checks for factual accuracy
- Validates citations
- Detects hallucinations
- Ensures safe content

**Tools**: None (review-focused)

## 📊 Data Flow

### Indexing Flow

```
Documents → Docling Parser → Chunker (512 tokens, 50 overlap)
    ↓
Metadata Extractor → Batch Processor (50 chunks/batch)
    ↓
Ollama Embeddings (nomic-embed-text, 768-dim)
    ↓
PostgreSQL + PGVector (IVFFlat index, cosine similarity)
```

### Retrieval Flow

```
User Query → Embedding Service (nomic-embed-text)
    ↓
Hybrid Search (Vector 60% + BM25 40%, RRF fusion)
    ↓
Retriever Agent (top 20 chunks)
    ↓
Reranker Agent (LLM-based scoring, top 5 chunks)
    ↓
Synthesizer Agent (generate answer with citations)
    ↓
Guardrails Agent (validate and approve)
    ↓
Response + Citations → User
```

## 🧪 Testing & Evaluation

### RAGAs Metrics

The system evaluates performance using four key metrics:

1. **Context Precision**: How relevant are the retrieved chunks?
2. **Context Recall**: Did we retrieve all necessary information?
3. **Faithfulness**: Is the answer grounded in the context?
4. **Answer Relevance**: Does the answer address the question?

### Running Evaluations

```bash
# Run evaluation
make evaluate

# View results
cat data/reports/evaluation_report_*.json
```

### Sample Evaluation Output

```
==========================================
RAG Evaluation Report
==========================================

Timestamp: 2024-01-15T10:30:00
Questions evaluated: 10

Metrics:
  Context Precision: 0.8750
  Context Recall:    0.9200
  Faithfulness:      0.9100
  Answer Relevancy:  0.8850
==========================================
```

## 🏗 Development

### Running Tests

```bash
# Backend tests
cd backend && pytest tests/

# Indexer tests
cd indexer && pytest tests/

# Evaluator tests
cd evaluator && pytest tests/
```

### Adding New Documents

```bash
# Add documents
cp /path/to/new/documents/*.pdf data/documents/

# Reindex
make index
```

## 📈 Performance Considerations

### Scaling Recommendations

**Development (Current Setup)**:
- Single node, all services co-located
- Suitable for < 10,000 documents
- < 100 concurrent users

**Production**:
- **Backend**: Horizontal scaling (multiple replicas behind load balancer)
- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL) with read replicas
- **Ollama**: Deploy on GPU-enabled instances, use model caching
- **Phoenix**: Separate instance for production observability

### Optimization Tips

1. **Indexing**: Increase `BATCH_SIZE` for faster embedding generation (if RAM allows)
2. **Retrieval**: Adjust `RETRIEVAL_TOP_K` based on document corpus size
3. **Memory**: Tune `MAX_MEMORY_TOKENS` for longer conversations
4. **Database**: Use HNSW index instead of IVFFlat for better accuracy (more memory)

## 🔒 Security Considerations

- **API Keys**: Store in environment variables, never commit
- **Database**: Use strong passwords, no external exposure in production
- **Input Validation**: Pydantic models validate all inputs
- **Rate Limiting**: Implement at API Gateway level in production
- **Content Filtering**: Guardrails agent checks for harmful content

## 🤝 Contributing

This is a production-grade reference implementation. Key areas for contribution:

- Additional document formats (HTML, PowerPoint, etc.)
- Advanced chunking strategies (agentic chunking, recursive summarization)
- Additional reranking models
- Multi-modal RAG (images, tables, charts)
- Real-time indexing via message queues

## 📄 License

This project uses open-source components. Ensure compliance with individual component licenses.

## 🙏 Acknowledgments

- **Docling**: Document processing
- **LlamaIndex**: RAG framework
- **CrewAI**: Agent orchestration
- **Arize Phoenix**: Observability
- **RAGAs**: Evaluation metrics
- **Ollama**: Local LLM hosting
- **OpenWebUI**: Chat interface

## 📞 Support

For issues and questions:

1. Review logs: `make logs`
2. Check service health: `make status`
3. Consult component documentation

---

**Built with production-grade engineering practices for enterprise deployment.**
