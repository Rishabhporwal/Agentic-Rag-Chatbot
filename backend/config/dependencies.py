from typing import Generator
from sqlalchemy.orm import Session
from database.connection import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm_service():
    """Dependency for LLM service."""
    from services.llm_service import LLMService
    from config.settings import settings
    return LLMService(
        base_url=settings.ollama_base_url,
        model=settings.llm_model
    )


def get_retrieval_service():
    """Dependency for retrieval service."""
    from services.retrieval_service import RetrievalService
    return RetrievalService()
