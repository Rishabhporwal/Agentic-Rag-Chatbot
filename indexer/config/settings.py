from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    database_url: str = "postgresql://rag_user:password@postgres:5432/agentic_rag"

    # Ollama configuration
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "nomic-embed-text"

    # Chunking configuration
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Embedding configuration
    batch_size: int = 50
    embedding_dim: int = 768

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
