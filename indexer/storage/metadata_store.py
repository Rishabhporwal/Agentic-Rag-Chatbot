import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .schema import Document


logger = logging.getLogger("indexer.metadata_store")


class MetadataStore:
    """Manages document metadata storage and retrieval."""

    def __init__(self, database_url: str):
        """
        Initialize the metadata store.

        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("MetadataStore initialized")

    def get_document_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document metadata by filename.

        Args:
            filename: Name of the document file

        Returns:
            Document metadata dictionary or None if not found
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter_by(filename=filename).first()
            if not doc:
                return None

            return {
                "id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "title": doc.title,
                "author": doc.author,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
                "metadata": doc.metadata
            }

        finally:
            session.close()

    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all documents with pagination.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of document metadata dictionaries
        """
        session = self.SessionLocal()
        try:
            docs = session.query(Document).limit(limit).offset(offset).all()

            return [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "title": doc.title,
                    "author": doc.author,
                    "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
                }
                for doc in docs
            ]

        finally:
            session.close()
