import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .schema import Base, Document, Chunk


logger = logging.getLogger("indexer.vector_store")


class VectorStore:
    """Manages storage of documents and chunks with embeddings in PostgreSQL + PGVector."""

    def __init__(self, database_url: str):
        """
        Initialize the vector store.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        logger.info("VectorStore initialized")

        # Verify connection and PGVector extension
        self._verify_setup()

    def _verify_setup(self):
        """Verify database connection and PGVector extension."""
        try:
            with self.engine.connect() as conn:
                # Check if PGVector extension is available
                result = conn.execute(text(
                    "SELECT * FROM pg_extension WHERE extname = 'vector'"
                ))
                if result.rowcount == 0:
                    raise RuntimeError("PGVector extension not installed")

                logger.info("Database connection and PGVector extension verified")

        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise

    def store_document(
        self,
        filename: str,
        file_type: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Store a document in the database.

        Args:
            filename: Name of the document file
            file_type: Type of the file (pdf, docx, etc.)
            title: Document title
            author: Document author
            created_at: Document creation date
            metadata: Additional metadata

        Returns:
            UUID of the stored document

        Raises:
            ValueError: If document with same filename already exists
        """
        session = self.SessionLocal()

        try:
            # Check if document already exists
            existing = session.query(Document).filter_by(filename=filename).first()
            if existing:
                logger.info(f"Document already exists: {filename}, using existing ID")
                return existing.id

            # Create new document
            doc = Document(
                filename=filename,
                file_type=file_type,
                title=title,
                author=author,
                created_at=created_at,
                metadata=metadata or {}
            )

            session.add(doc)
            session.commit()
            session.refresh(doc)

            logger.info(f"Stored document: {filename} (ID: {doc.id})")
            return doc.id

        except Exception as e:
            session.rollback()
            logger.error(f"Error storing document: {str(e)}")
            raise

        finally:
            session.close()

    def store_chunk(
        self,
        document_id: uuid.UUID,
        content: str,
        embedding: List[float],
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Store a chunk with its embedding.

        Args:
            document_id: UUID of the parent document
            content: Chunk content text
            embedding: Embedding vector
            chunk_index: Index of this chunk in the document
            metadata: Additional metadata

        Returns:
            UUID of the stored chunk
        """
        session = self.SessionLocal()

        try:
            # Create chunk record using raw SQL for vector type
            chunk_id = uuid.uuid4()
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            query = text("""
                INSERT INTO chunks (id, document_id, content, embedding, chunk_index, metadata)
                VALUES (:id, :document_id, :content, :embedding::vector, :chunk_index, :metadata)
            """)

            session.execute(query, {
                "id": str(chunk_id),
                "document_id": str(document_id),
                "content": content,
                "embedding": embedding_str,
                "chunk_index": chunk_index,
                "metadata": metadata or {}
            })

            session.commit()

            logger.debug(f"Stored chunk {chunk_index} for document {document_id}")
            return chunk_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error storing chunk: {str(e)}")
            raise

        finally:
            session.close()

    def store_document_with_chunks(
        self,
        document_data: Dict[str, Any],
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store a document along with all its chunks.

        Args:
            document_data: Document metadata dictionary
            chunks: List of chunk dictionaries with embeddings

        Returns:
            Dictionary with statistics about the storage operation
        """
        logger.info(f"Storing document with {len(chunks)} chunks")

        # Store document
        doc_id = self.store_document(
            filename=document_data.get("filename"),
            file_type=document_data.get("file_type"),
            title=document_data.get("title"),
            author=document_data.get("author"),
            created_at=document_data.get("created_at"),
            metadata=document_data.get("metadata", {})
        )

        # Store chunks
        stored_chunks = 0
        failed_chunks = 0

        for chunk in chunks:
            try:
                if "embedding" not in chunk:
                    logger.warning(f"Chunk {chunk.get('chunk_index')} has no embedding, skipping")
                    failed_chunks += 1
                    continue

                self.store_chunk(
                    document_id=doc_id,
                    content=chunk["content"],
                    embedding=chunk["embedding"],
                    chunk_index=chunk.get("chunk_index", 0),
                    metadata=chunk.get("metadata", {})
                )
                stored_chunks += 1

            except Exception as e:
                logger.error(f"Failed to store chunk {chunk.get('chunk_index')}: {str(e)}")
                failed_chunks += 1

        result = {
            "document_id": str(doc_id),
            "filename": document_data.get("filename"),
            "total_chunks": len(chunks),
            "stored_chunks": stored_chunks,
            "failed_chunks": failed_chunks
        }

        logger.info(
            f"Document storage complete: {stored_chunks}/{len(chunks)} chunks stored"
        )

        return result

    def get_document_count(self) -> int:
        """Get the total number of documents in the database."""
        session = self.SessionLocal()
        try:
            count = session.query(Document).count()
            return count
        finally:
            session.close()

    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the database."""
        session = self.SessionLocal()
        try:
            result = session.execute(text("SELECT COUNT(*) FROM chunks"))
            count = result.scalar()
            return count
        finally:
            session.close()
