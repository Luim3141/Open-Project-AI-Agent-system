-- QLDAPM Local Second Brain Knowledge Storage Schema
-- Completely isolated from OpenProject's business tables in public schema

CREATE SCHEMA IF NOT EXISTS qldapm_knowledge;

CREATE TABLE IF NOT EXISTS qldapm_knowledge.knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    doc_type VARCHAR(32) NOT NULL,
    source_id VARCHAR(256) NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    allowed_roles TEXT[] NOT NULL DEFAULT ARRAY['PM', 'BA', 'FE', 'BE', 'QA'],
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_tsv TSVECTOR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS qldapm_knowledge.knowledge_chunks (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) REFERENCES qldapm_knowledge.knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tsv TSVECTOR,
    chunk_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kdoc_project ON qldapm_knowledge.knowledge_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_kdoc_type ON qldapm_knowledge.knowledge_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_kdoc_source ON qldapm_knowledge.knowledge_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_kdoc_tsv ON qldapm_knowledge.knowledge_documents USING GIN(content_tsv);
CREATE INDEX IF NOT EXISTS idx_kchunks_tsv ON qldapm_knowledge.knowledge_chunks USING GIN(chunk_tsv);
