import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger("indexer.metadata_extractor")


class MetadataExtractor:
    """Extracts and enriches document metadata."""

    def __init__(self):
        """Initialize the metadata extractor."""
        logger.info("MetadataExtractor initialized")

    def extract_metadata(
        self,
        document: Dict[str, Any],
        file_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Extract and enrich metadata from a document.

        Args:
            document: Document dictionary
            file_path: Optional path to the source file

        Returns:
            Dictionary containing enriched metadata
        """
        metadata = document.get("metadata", {}).copy()

        # Add extraction timestamp
        metadata["indexed_at"] = datetime.utcnow().isoformat()

        # Extract file information if path provided
        if file_path and file_path.exists():
            stat = file_path.stat()
            metadata["file_size"] = stat.st_size
            metadata["file_created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            metadata["file_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Extract title if not present
        if "title" not in metadata and "title" in document:
            metadata["title"] = document["title"]

        # Extract author if not present
        if "author" not in metadata and "author" in document:
            metadata["author"] = document["author"]

        # Add file type information
        if "file_type" in document:
            metadata["file_type"] = document["file_type"]

        # Add content statistics
        content = document.get("content", "")
        if content:
            metadata["content_length"] = len(content)
            metadata["word_count"] = len(content.split())
            metadata["line_count"] = len(content.splitlines())

        logger.debug(f"Extracted metadata for: {document.get('filename')}")
        return metadata

    def enrich_chunk_metadata(
        self,
        chunk: Dict[str, Any],
        document: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """
        Enrich chunk metadata with document-level information.

        Args:
            chunk: Chunk dictionary
            document: Parent document dictionary
            chunk_index: Index of this chunk in the document

        Returns:
            Enriched metadata dictionary
        """
        metadata = chunk.get("metadata", {}).copy()

        # Add document-level information
        metadata["document_filename"] = document.get("filename")
        metadata["document_title"] = document.get("title")
        metadata["document_author"] = document.get("author")
        metadata["document_file_type"] = document.get("file_type")

        # Add chunk-level information
        metadata["chunk_index"] = chunk_index
        metadata["char_count"] = chunk.get("char_count", 0)
        metadata["token_count"] = chunk.get("token_count", 0)

        # Try to extract section information from content
        content = chunk.get("content", "")
        section = self._extract_section(content)
        if section:
            metadata["section"] = section

        return metadata

    def _extract_section(self, content: str) -> Optional[str]:
        """
        Extract section/heading information from chunk content.

        Args:
            content: Chunk content

        Returns:
            Section name if found, None otherwise
        """
        # Look for markdown headers
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line.startswith('#'):
                # Remove markdown header symbols
                return line.lstrip('#').strip()

        return None
