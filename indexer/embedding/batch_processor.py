import logging
from typing import List, Dict, Any
from tqdm import tqdm


logger = logging.getLogger("indexer.batch_processor")


class BatchProcessor:
    """Processes chunks in batches for efficient embedding generation."""

    def __init__(self, embedder, batch_size: int = 50):
        """
        Initialize the batch processor.

        Args:
            embedder: Embedder instance for generating embeddings
            batch_size: Number of chunks to process in each batch
        """
        self.embedder = embedder
        self.batch_size = batch_size
        logger.info(f"BatchProcessor initialized (batch_size={batch_size})")

    def process_chunks(
        self,
        chunks: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process chunks in batches and add embeddings.

        Args:
            chunks: List of chunk dictionaries
            show_progress: Whether to show progress bar

        Returns:
            List of chunks with embeddings added
        """
        if not chunks:
            logger.warning("No chunks to process")
            return []

        logger.info(f"Processing {len(chunks)} chunks in batches of {self.batch_size}")

        # Create batches
        batches = [
            chunks[i:i + self.batch_size]
            for i in range(0, len(chunks), self.batch_size)
        ]

        processed_chunks = []
        failed_count = 0

        # Process each batch
        iterator = tqdm(batches, desc="Processing batches") if show_progress else batches

        for batch in iterator:
            # Extract content from batch
            texts = [chunk["content"] for chunk in batch]

            try:
                # Generate embeddings for batch
                embeddings = self.embedder.embed_batch(texts)

                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    if embedding is not None:
                        chunk["embedding"] = embedding
                        processed_chunks.append(chunk)
                    else:
                        logger.warning(
                            f"Failed to generate embedding for chunk "
                            f"{chunk.get('metadata', {}).get('document_filename', 'unknown')}"
                        )
                        failed_count += 1

            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                failed_count += len(batch)
                continue

        logger.info(
            f"Processed {len(processed_chunks)} chunks successfully, "
            f"{failed_count} failed"
        )

        return processed_chunks

    def process_single_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single chunk and add embedding.

        Args:
            chunk: Chunk dictionary

        Returns:
            Chunk with embedding added

        Raises:
            RuntimeError: If embedding generation fails
        """
        content = chunk.get("content")
        if not content:
            raise ValueError("Chunk has no content")

        try:
            embedding = self.embedder.embed_text(content)
            chunk["embedding"] = embedding
            return chunk

        except Exception as e:
            logger.error(f"Failed to process chunk: {str(e)}")
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
