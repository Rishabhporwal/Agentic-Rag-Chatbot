import logging
import re
from typing import List, Dict, Any
import tiktoken


logger = logging.getLogger("indexer.chunker")


class Chunker:
    """Splits documents into chunks with overlap and semantic boundaries."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        logger.info(
            f"Chunker initialized (size={chunk_size}, overlap={chunk_overlap})"
        )

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.tokenizer.encode(text))

    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex for semantic boundaries.

        Args:
            text: Input text to split

        Returns:
            List of sentences
        """
        # Split on sentence boundaries (., !, ?) followed by whitespace
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(
        self,
        document: Dict[str, Any],
        preserve_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into smaller pieces with overlap.

        Args:
            document: Document dictionary with 'content' and metadata
            preserve_metadata: Whether to include document metadata in chunks

        Returns:
            List of chunk dictionaries
        """
        content = document.get("content", "")
        if not content:
            logger.warning(f"Empty content for document: {document.get('filename')}")
            return []

        logger.info(f"Chunking document: {document.get('filename')}")

        # Split into sentences for semantic boundaries
        sentences = self.split_by_sentences(content)

        chunks = []
        current_chunk = []
        current_token_count = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence exceeds chunk size, split it further
            if sentence_tokens > self.chunk_size:
                # Add current chunk if it has content
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_token_count = 0

                # Split long sentence by words
                words = sentence.split()
                temp_chunk = []
                temp_token_count = 0

                for word in words:
                    word_tokens = self.count_tokens(word)
                    if temp_token_count + word_tokens > self.chunk_size:
                        if temp_chunk:
                            chunks.append(" ".join(temp_chunk))
                        temp_chunk = [word]
                        temp_token_count = word_tokens
                    else:
                        temp_chunk.append(word)
                        temp_token_count += word_tokens

                if temp_chunk:
                    chunks.append(" ".join(temp_chunk))

            # If adding sentence would exceed chunk size, start new chunk
            elif current_token_count + sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Calculate how many sentences to include in overlap
                    overlap_sentences = []
                    overlap_tokens = 0

                    for sent in reversed(current_chunk):
                        sent_tokens = self.count_tokens(sent)
                        if overlap_tokens + sent_tokens <= self.chunk_overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_tokens += sent_tokens
                        else:
                            break

                    current_chunk = overlap_sentences + [sentence]
                    current_token_count = overlap_tokens + sentence_tokens
                else:
                    current_chunk = [sentence]
                    current_token_count = sentence_tokens

            else:
                current_chunk.append(sentence)
                current_token_count += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Create chunk dictionaries with metadata
        chunk_dicts = []
        for idx, chunk_content in enumerate(chunks):
            chunk_dict = {
                "content": chunk_content,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "char_count": len(chunk_content),
                "token_count": self.count_tokens(chunk_content),
            }

            # Preserve document metadata if requested
            if preserve_metadata:
                chunk_dict["metadata"] = {
                    "document_filename": document.get("filename"),
                    "document_title": document.get("title"),
                    "document_author": document.get("author"),
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }

                # Copy over custom metadata
                if "metadata" in document:
                    for key, value in document["metadata"].items():
                        if key not in chunk_dict["metadata"]:
                            chunk_dict["metadata"][key] = value

            chunk_dicts.append(chunk_dict)

        logger.info(
            f"Created {len(chunk_dicts)} chunks for document: "
            f"{document.get('filename')}"
        )

        return chunk_dicts
