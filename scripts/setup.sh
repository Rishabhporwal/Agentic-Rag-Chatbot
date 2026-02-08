#!/bin/bash

set -e

echo "========================================="
echo "  Agentic RAG System - Setup Script"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

echo "✓ Docker and docker-compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "WARNING: Please edit .env file and set a secure POSTGRES_PASSWORD"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/documents data/logs data/reports
touch data/documents/.gitkeep data/logs/.gitkeep data/reports/.gitkeep
echo "✓ Data directories created"
echo ""

# Start services
echo "Starting Docker services..."
docker-compose up -d postgres ollama phoenix
echo "✓ Core services started"
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
while ! docker-compose exec -T postgres pg_isready -U rag_user -d agentic_rag > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Error: PostgreSQL failed to start after $max_attempts attempts"
        exit 1
    fi
    echo "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 2
done
echo "✓ PostgreSQL is ready"
echo ""

# Pull Ollama models
echo "Pulling Ollama models (this may take a while)..."
bash scripts/pull_models.sh
echo "✓ Ollama models pulled"
echo ""

# Build backend Docker image
echo "Building backend Docker image..."
docker-compose build backend
echo "✓ Backend image built"
echo ""

# Start remaining services
echo "Starting remaining services..."
docker-compose up -d
echo "✓ All services started"
echo ""

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10
echo ""

echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Services are now running:"
echo "  - OpenWebUI:  http://localhost:3000"
echo "  - Phoenix UI: http://localhost:6006"
echo "  - Backend API: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "Next steps:"
echo "  1. Place documents in ./data/documents/"
echo "  2. Run: make index"
echo "  3. Access OpenWebUI at http://localhost:3000"
echo ""
echo "View logs: make logs"
echo "Stop services: make down"
echo ""
