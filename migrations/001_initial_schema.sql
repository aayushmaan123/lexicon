-- Lexicon Initial Database Schema
-- Migration: 001_initial_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_upload_date ON documents(upload_date);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);

-- Parsed Documents table
CREATE TABLE parsed_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    title TEXT,
    author TEXT,
    summary TEXT,
    key_points JSONB,
    parties JSONB,
    dates JSONB,
    document_type VARCHAR(100),
    total_pages INTEGER,
    total_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parsed_documents_document_id ON parsed_documents(document_id);
CREATE INDEX idx_parsed_documents_document_type ON parsed_documents(document_type);

-- Document Chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    token_count INTEGER,
    embedding_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding_id ON document_chunks(embedding_id);

-- Contracts table
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    contract_type VARCHAR(100),
    effective_date DATE,
    expiration_date DATE,
    jurisdiction VARCHAR(100),
    governing_law TEXT,
    risk_level VARCHAR(20),
    overall_assessment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contracts_document_id ON contracts(document_id);
CREATE INDEX idx_contracts_risk_level ON contracts(risk_level);

-- Parties table
CREATE TABLE parties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    party_name VARCHAR(255) NOT NULL,
    party_type VARCHAR(50),
    role VARCHAR(100),
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parties_contract_id ON parties(contract_id);

-- Clauses table
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    clause_type VARCHAR(100) NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    page_number INTEGER,
    risk_level VARCHAR(20),
    unusual BOOLEAN DEFAULT FALSE,
    obligations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clauses_contract_id ON clauses(contract_id);
CREATE INDEX idx_clauses_clause_type ON clauses(clause_type);
CREATE INDEX idx_clauses_risk_level ON clauses(risk_level);

-- Risk Assessments table
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    clause_id UUID REFERENCES clauses(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_assessments_contract_id ON risk_assessments(contract_id);
CREATE INDEX idx_risk_assessments_severity ON risk_assessments(severity);

-- Research Queries table
CREATE TABLE research_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    jurisdiction VARCHAR(100),
    query_type VARCHAR(50),
    user_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_queries_created_at ON research_queries(created_at);

-- Research Results table
CREATE TABLE research_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES research_queries(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    sources JSONB NOT NULL,
    citations JSONB,
    relevance_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_results_query_id ON research_results(query_id);

-- Case Law table
CREATE TABLE case_law (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_name VARCHAR(500) NOT NULL,
    citation TEXT NOT NULL,
    court VARCHAR(255),
    decision_date DATE,
    jurisdiction VARCHAR(100),
    summary TEXT,
    key_holdings JSONB,
    full_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_case_law_citation ON case_law(citation);
CREATE INDEX idx_case_law_jurisdiction ON case_law(jurisdiction);
CREATE INDEX idx_case_law_decision_date ON case_law(decision_date);

-- Statutes table
CREATE TABLE statutes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    citation TEXT NOT NULL,
    jurisdiction VARCHAR(100),
    effective_date DATE,
    summary TEXT,
    full_text TEXT,
    section_number VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statutes_citation ON statutes(citation);
CREATE INDEX idx_statutes_jurisdiction ON statutes(jurisdiction);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parsed_documents_updated_at BEFORE UPDATE ON parsed_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
