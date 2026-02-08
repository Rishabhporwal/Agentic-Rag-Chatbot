.PHONY: help setup up down restart logs clean pull-models index evaluate test

help:
	@echo "Agentic RAG System - Available Commands:"
	@echo ""
	@echo "  make setup         - Initial setup (copy .env, create directories)"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs from all services"
	@echo "  make logs-backend  - View backend logs"
	@echo "  make logs-postgres - View PostgreSQL logs"
	@echo "  make pull-models   - Pull Ollama models"
	@echo "  make index         - Run document indexer"
	@echo "  make evaluate      - Run RAG evaluator"
	@echo "  make clean         - Remove all containers and volumes"
	@echo "  make test          - Run tests"
	@echo ""

setup:
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env file created"; else echo ".env already exists"; fi
	@mkdir -p data/documents data/logs data/reports
	@touch data/documents/.gitkeep data/logs/.gitkeep data/reports/.gitkeep
	@echo "Setup complete! Please edit .env file with your configuration."

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Waiting for health checks..."
	@sleep 10
	@echo "Access OpenWebUI at http://localhost:3000"
	@echo "Access Phoenix at http://localhost:6006"
	@echo "Backend API at http://localhost:8000"

down:
	@echo "Stopping services..."
	docker-compose down

restart:
	@echo "Restarting services..."
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-postgres:
	docker-compose logs -f postgres

logs-ollama:
	docker-compose logs -f ollama

pull-models:
	@echo "Pulling Ollama models..."
	@bash scripts/pull_models.sh

index:
	@echo "Running document indexer..."
	@docker-compose run --rm -v $(PWD)/data/documents:/data/documents indexer python main.py --input /data/documents

evaluate:
	@echo "Running RAG evaluator..."
	@docker-compose run --rm evaluator python main.py

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "Cleanup complete"

test:
	@echo "Running tests..."
	@cd backend && python -m pytest tests/
	@cd indexer && python -m pytest tests/
	@cd evaluator && python -m pytest tests/

build:
	@echo "Building Docker images..."
	docker-compose build

status:
	@echo "Service status:"
	@docker-compose ps
