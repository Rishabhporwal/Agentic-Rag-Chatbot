import logging
from pathlib import Path
from typing import List, Dict, Any
from docling.document_converter import DocumentConverter


logger = logging.getLogger("indexer.document_loader")


class DocumentLoader:
    """Loads and parses documents using Docling."""

    def __init__(self):
        """Initialize the document loader with Docling converter."""
        self.converter = DocumentConverter()
        logger.info("DocumentLoader initialized")

    def load_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Load a single document and extract its content.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing document content and metadata

        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check if file type is supported
        supported_extensions = {".pdf", ".docx", ".doc", ".txt", ".md"}
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported types: {supported_extensions}"
            )

        try:
            logger.info(f"Loading document: {file_path.name}")

            # Convert document using Docling
            result = self.converter.convert(str(file_path))

            # Extract content and metadata
            document_data = {
                "filename": file_path.name,
                "file_type": file_path.suffix.lstrip('.'),
                "content": result.document.export_to_markdown(),
                "metadata": {
                    "file_size": file_path.stat().st_size,
                    "file_path": str(file_path),
                },
            }

            # Extract additional metadata from Docling result if available
            if hasattr(result.document, 'meta'):
                meta = result.document.meta
                if hasattr(meta, 'title') and meta.title:
                    document_data["title"] = meta.title
                if hasattr(meta, 'author') and meta.author:
                    document_data["author"] = meta.author
                if hasattr(meta, 'date') and meta.date:
                    document_data["created_at"] = meta.date

            logger.info(f"Successfully loaded document: {file_path.name}")
            return document_data

        except Exception as e:
            logger.error(f"Error loading document {file_path.name}: {str(e)}")
            raise

    def load_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Load all supported documents from a directory.

        Args:
            directory: Path to the directory containing documents

        Returns:
            List of document data dictionaries
        """
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        logger.info(f"Loading documents from: {directory}")

        documents = []
        supported_extensions = {".pdf", ".docx", ".doc", ".txt", ".md"}

        # Find all supported files
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    doc_data = self.load_document(file_path)
                    documents.append(doc_data)
                except Exception as e:
                    logger.warning(f"Skipping {file_path.name}: {str(e)}")
                    continue

        logger.info(f"Loaded {len(documents)} documents from directory")
        return documents
