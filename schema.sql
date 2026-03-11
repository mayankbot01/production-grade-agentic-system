-- Production Grade Agentic System Database Schema
-- PostgreSQL Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- CONVERSATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- ============================================================
-- MESSAGES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_role ON messages(role);

-- ============================================================
-- AGENT_RUNS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    run_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    token_usage JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_run_type ON agent_runs(run_type);
CREATE INDEX idx_agent_runs_started_at ON agent_runs(started_at DESC);

-- ============================================================
-- TOOL_EXECUTIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_input JSONB NOT NULL,
    tool_output JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tool_executions_agent_run_id ON tool_executions(agent_run_id);
CREATE INDEX idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_status ON tool_executions(status);

-- ============================================================
-- MEMORY TABLE (Long-term agent memory)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    memory_type VARCHAR(100) NOT NULL DEFAULT 'episodic',
    content TEXT NOT NULL,
    embedding JSONB,
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agent_memory_session_id ON agent_memory(session_id);
CREATE INDEX idx_agent_memory_memory_type ON agent_memory(memory_type);
CREATE INDEX idx_agent_memory_importance ON agent_memory(importance_score DESC);

-- ============================================================
-- EVALUATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    eval_type VARCHAR(100) NOT NULL,
    score FLOAT,
    passed BOOLEAN,
    details JSONB DEFAULT '{}',
    evaluator VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evaluations_agent_run_id ON evaluations(agent_run_id);
CREATE INDEX idx_evaluations_eval_type ON evaluations(eval_type);

-- ============================================================
-- RATE_LIMITS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identifier VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier, endpoint)
);

CREATE INDEX idx_rate_limits_identifier ON rate_limits(identifier);

-- ============================================================
-- TRIGGERS for updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
