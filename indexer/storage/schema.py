from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid


Base = declarative_base()


class Document(Base):
    """Document table schema."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, unique=True)
    file_type = Column(String(50))
    title = Column(Text)
    author = Column(String(255))
    created_at = Column(TIMESTAMP)
    indexed_at = Column(TIMESTAMP, server_default=func.now())
    metadata = Column(JSON, default={})


class Chunk(Base):
    """Chunk table schema."""

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    # Note: embedding column is handled by PGVector, not defined here
    chunk_index = Column(Integer, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP, server_default=func.now())
