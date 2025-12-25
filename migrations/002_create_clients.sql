-- Migration 002: Create clients table

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status client_status NOT NULL DEFAULT 'active',
    color_hex TEXT NOT NULL DEFAULT '#a855f7',
    default_priority_weight INTEGER NOT NULL DEFAULT 0 CHECK (default_priority_weight >= 0 AND default_priority_weight <= 20),
    health_status health_status,
    last_touched_at TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_clients_status ON clients(status) WHERE archived_at IS NULL;
CREATE INDEX idx_clients_name ON clients(LOWER(name));
CREATE INDEX idx_clients_archived ON clients(archived_at) WHERE archived_at IS NOT NULL;

-- Trigger for updated_at
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Full-text search on client name
ALTER TABLE clients ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(notes, ''))) STORED;

CREATE INDEX idx_clients_search ON clients USING GIN(search_vector);
