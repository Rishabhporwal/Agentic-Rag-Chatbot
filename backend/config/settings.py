from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "Agentic RAG Backend"
    environment: str = "production"
    log_level: str = "INFO"

    # Database configuration
    database_url: str = "postgresql://rag_user:password@postgres:5432/agentic_rag"

    # Ollama configuration
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "llama3.1:8b-instruct-q4_K_M"
    reranker_model: str = "qllama/bge-reranker-v2-m3"

    # Phoenix configuration
    phoenix_collector_endpoint: str = "http://phoenix:6006"

    # Retrieval configuration
    retrieval_top_k: int = 20
    rerank_top_k: int = 5
    final_top_k: int = 3
    vector_weight: float = 0.6
    bm25_weight: float = 0.4

    # Memory configuration
    max_memory_messages: int = 10
    max_memory_tokens: int = 4096

    # Generation configuration
    default_temperature: float = 0.7
    default_max_tokens: int = 2048

    # API configuration
    api_v1_prefix: str = "/v1"
    cors_origins: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
