#!/usr/bin/env python3
"""
Document Indexer Application

This application ingests documents, chunks them, generates embeddings,
and stores them in PostgreSQL with PGVector for retrieval.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from config import settings, setup_logging
from ingestion import DocumentLoader, Chunker, MetadataExtractor
from embedding import Embedder, BatchProcessor
from storage import VectorStore
from utils import validate_directory


def main():
    """Main entry point for the indexer application."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Index documents for Agentic RAG system"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to directory containing documents to index"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.batch_size,
        help=f"Batch size for embedding generation (default: {settings.batch_size})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level (default: {settings.log_level})"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(level=args.log_level)
    logger.info("=" * 60)
    logger.info("Document Indexer - Agentic RAG System")
    logger.info("=" * 60)

    try:
        # Validate input directory
        input_dir = validate_directory(args.input)
        logger.info(f"Input directory: {input_dir}")

        # Initialize components
        logger.info("Initializing components...")
        document_loader = DocumentLoader()
        chunker = Chunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        metadata_extractor = MetadataExtractor()
        embedder = Embedder(
            base_url=settings.ollama_base_url,
            model=settings.embedding_model
        )
        batch_processor = BatchProcessor(embedder, batch_size=args.batch_size)
        vector_store = VectorStore(settings.database_url)

        # Load documents
        logger.info("Loading documents...")
        start_time = time.time()
        documents = document_loader.load_directory(input_dir)

        if not documents:
            logger.warning("No documents found in directory")
            return 0

        logger.info(f"Loaded {len(documents)} documents")

        # Process each document
        total_chunks = 0
        successful_docs = 0
        failed_docs = 0

        for idx, doc in enumerate(documents, 1):
            logger.info(f"\nProcessing document {idx}/{len(documents)}: {doc['filename']}")

            try:
                # Extract metadata
                metadata = metadata_extractor.extract_metadata(doc)
                doc["metadata"] = metadata

                # Chunk document
                chunks = chunker.chunk_document(doc)
                if not chunks:
                    logger.warning(f"No chunks generated for {doc['filename']}")
                    failed_docs += 1
                    continue

                logger.info(f"Generated {len(chunks)} chunks")

                # Generate embeddings
                chunks_with_embeddings = batch_processor.process_chunks(
                    chunks,
                    show_progress=True
                )

                if not chunks_with_embeddings:
                    logger.warning(f"No embeddings generated for {doc['filename']}")
                    failed_docs += 1
                    continue

                # Store in database
                result = vector_store.store_document_with_chunks(doc, chunks_with_embeddings)

                logger.info(
                    f"Stored {result['stored_chunks']}/{result['total_chunks']} chunks"
                )

                total_chunks += result['stored_chunks']
                successful_docs += 1

            except Exception as e:
                logger.error(f"Failed to process document {doc['filename']}: {str(e)}")
                failed_docs += 1
                continue

        # Calculate statistics
        elapsed_time = time.time() - start_time
        docs_per_sec = len(documents) / elapsed_time if elapsed_time > 0 else 0
        chunks_per_sec = total_chunks / elapsed_time if elapsed_time > 0 else 0

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Indexing Complete!")
        logger.info("=" * 60)
        logger.info(f"Total documents processed: {len(documents)}")
        logger.info(f"Successful: {successful_docs}")
        logger.info(f"Failed: {failed_docs}")
        logger.info(f"Total chunks stored: {total_chunks}")
        logger.info(f"Time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Documents per second: {docs_per_sec:.2f}")
        logger.info(f"Chunks per second: {chunks_per_sec:.2f}")

        # Get database statistics
        doc_count = vector_store.get_document_count()
        chunk_count = vector_store.get_chunk_count()
        logger.info(f"\nDatabase totals:")
        logger.info(f"Total documents in database: {doc_count}")
        logger.info(f"Total chunks in database: {chunk_count}")
        logger.info("=" * 60)

        return 0 if failed_docs == 0 else 1

    except KeyboardInterrupt:
        logger.info("\nIndexing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
