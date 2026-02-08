-- Agentic RAG Database Initialization Script
-- This script sets up the PostgreSQL database with PGVector extension

-- Enable PGVector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    title TEXT,
    author VARCHAR(255),
    created_at TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_filename UNIQUE (filename)
);

-- Create index on filename for faster lookups
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

-- Create chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),  -- nomic-embed-text produces 768-dimensional vectors
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create vector similarity index using IVFFlat
-- Lists parameter set to 100 for good balance (adjust based on dataset size)
-- Use HNSW for better accuracy but more memory: CREATE INDEX ... USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create index for document relationship
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

-- Create index for chunk ordering
CREATE INDEX IF NOT EXISTS idx_chunks_document_chunk ON chunks(document_id, chunk_index);

-- Create GIN index on metadata for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN(metadata);

-- Create full-text search index for BM25-style keyword search
CREATE INDEX IF NOT EXISTS idx_chunks_content_fts ON chunks
    USING GIN(to_tsvector('english', content));

-- Create conversations table for session management
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create index on session_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Create messages table for conversation history
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Create index for conversation ordering
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);

-- Create function to update conversation updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update conversation timestamp
DROP TRIGGER IF EXISTS trigger_update_conversation_timestamp ON messages;
CREATE TRIGGER trigger_update_conversation_timestamp
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();

-- Create Phoenix database for observability (separate database)
CREATE DATABASE phoenix;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE agentic_rag TO rag_user;
GRANT ALL PRIVILEGES ON DATABASE phoenix TO rag_user;

-- Create helper function for vector similarity search
CREATE OR REPLACE FUNCTION search_chunks_by_embedding(
    query_embedding vector(768),
    match_count integer DEFAULT 20,
    filter_metadata jsonb DEFAULT '{}'
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata
    FROM chunks c
    WHERE
        (filter_metadata = '{}' OR c.metadata @> filter_metadata)
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create helper function for hybrid search (vector + BM25)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(768),
    query_text TEXT,
    match_count integer DEFAULT 20,
    vector_weight FLOAT DEFAULT 0.6,
    bm25_weight FLOAT DEFAULT 0.4
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    combined_score FLOAT,
    vector_score FLOAT,
    bm25_score FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.metadata,
            1 - (c.embedding <=> query_embedding) AS score
        FROM chunks c
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    bm25_search AS (
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.metadata,
            ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) AS score
        FROM chunks c
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
        ORDER BY score DESC
        LIMIT match_count * 2
    )
    SELECT
        COALESCE(v.id, b.id) AS chunk_id,
        COALESCE(v.document_id, b.document_id) AS document_id,
        COALESCE(v.content, b.content) AS content,
        (COALESCE(v.score, 0) * vector_weight + COALESCE(b.score, 0) * bm25_weight) AS combined_score,
        COALESCE(v.score, 0) AS vector_score,
        COALESCE(b.score, 0) AS bm25_score,
        COALESCE(v.metadata, b.metadata) AS metadata
    FROM vector_search v
    FULL OUTER JOIN bm25_search b ON v.id = b.id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Insert sample system message for testing
INSERT INTO conversations (session_id, metadata)
VALUES ('test-session', '{"purpose": "testing"}')
ON CONFLICT (session_id) DO NOTHING;

-- Create stats view for monitoring
CREATE OR REPLACE VIEW chunk_stats AS
SELECT
    COUNT(*) as total_chunks,
    COUNT(DISTINCT document_id) as total_documents,
    AVG(LENGTH(content)) as avg_content_length,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedded_chunks
FROM chunks;

CREATE OR REPLACE VIEW conversation_stats AS
SELECT
    COUNT(*) as total_conversations,
    COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '24 hours') as active_24h,
    AVG(msg_count) as avg_messages_per_conversation
FROM (
    SELECT
        c.id,
        c.updated_at,
        COUNT(m.id) as msg_count
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    GROUP BY c.id, c.updated_at
) subq;

-- Vacuum and analyze for optimal performance
VACUUM ANALYZE documents;
VACUUM ANALYZE chunks;
VACUUM ANALYZE conversations;
VACUUM ANALYZE messages;

-- Display initialization summary
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE 'Extensions: vector, uuid-ossp';
    RAISE NOTICE 'Tables: documents, chunks, conversations, messages';
    RAISE NOTICE 'Indexes: Vector (IVFFlat), FTS, JSONB';
    RAISE NOTICE 'Functions: search_chunks_by_embedding, hybrid_search';
END $$;
