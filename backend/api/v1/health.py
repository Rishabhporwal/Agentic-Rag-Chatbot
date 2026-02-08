from fastapi import APIRouter
from datetime import datetime
import requests
from config.settings import settings
from models.responses import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns status of the API and dependent services.
    """
    services = {
        "database": "unknown",
        "ollama": "unknown",
        "phoenix": "unknown"
    }

    # Check Ollama
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            services["ollama"] = "healthy"
        else:
            services["ollama"] = "unhealthy"
    except Exception:
        services["ollama"] = "unreachable"

    # Check database (basic check)
    try:
        from database.connection import engine
        async with engine.connect() as conn:
            services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"

    # Check Phoenix (optional)
    try:
        response = requests.get(f"{settings.phoenix_collector_endpoint}", timeout=2)
        services["phoenix"] = "healthy"
    except Exception:
        services["phoenix"] = "unreachable"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        services=services,
        version="1.0.0"
    )
