"""
Agentic RAG Backend API

FastAPI application for the Agentic RAG system with CrewAI orchestration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from utils.logger import setup_logging
from api.v1 import chat, conversations, health, documents


# Setup logging
setup_logging(level=settings.log_level)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)

    # Initialize Phoenix (optional, may not be available)
    try:
        from services.phoenix_service import PhoenixService
        phoenix = PhoenixService(settings.phoenix_collector_endpoint)
        phoenix.initialize()
    except Exception as e:
        logger.warning(f"Phoenix initialization skipped: {str(e)}")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-grade Agentic RAG system with CrewAI orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(chat.router, prefix=settings.api_v1_prefix, tags=["chat"])
app.include_router(conversations.router, prefix=settings.api_v1_prefix, tags=["conversations"])
app.include_router(documents.router, prefix=settings.api_v1_prefix, tags=["documents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
