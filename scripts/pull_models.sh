#!/bin/bash

set -e

echo "========================================="
echo "  Pulling Ollama Models"
echo "========================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default models
EMBEDDING_MODEL=${EMBEDDING_MODEL:-"nomic-embed-text"}
LLM_MODEL=${LLM_MODEL:-"llama3.1:8b-instruct-q4_K_M"}
RERANKER_MODEL=${RERANKER_MODEL:-"qllama/bge-reranker-v2-m3"}

# Pull embedding model
echo "Pulling embedding model: $EMBEDDING_MODEL"
docker-compose exec -T ollama ollama pull $EMBEDDING_MODEL
echo "✓ Embedding model pulled"
echo ""

# Pull LLM model
echo "Pulling LLM model: $LLM_MODEL"
docker-compose exec -T ollama ollama pull $LLM_MODEL
echo "✓ LLM model pulled"
echo ""

# Pull reranker model (optional, may not exist in Ollama)
echo "Pulling reranker model: $RERANKER_MODEL (optional)"
docker-compose exec -T ollama ollama pull $RERANKER_MODEL || echo "Note: Reranker model not available, will use LLM-based reranking"
echo ""

# List installed models
echo "Installed models:"
docker-compose exec -T ollama ollama list
echo ""

echo "========================================="
echo "  Model pulling complete!"
echo "========================================="
