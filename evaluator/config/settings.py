from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Evaluator settings."""

    # Backend API configuration
    backend_url: str = "http://backend:8000"
    api_v1_prefix: str = "/v1"

    # Evaluation configuration
    test_dataset_path: str = "datasets/qa_pairs.json"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
