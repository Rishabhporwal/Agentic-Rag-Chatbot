from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Create engine
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
