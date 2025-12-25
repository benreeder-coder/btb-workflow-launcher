-- Migration 008: Create calls table for Fireflies transcript summaries

CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Fireflies identifier (for idempotency)
    fireflies_id TEXT UNIQUE NOT NULL,

    -- Client mapping
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,

    -- Call details
    title TEXT NOT NULL,
    call_date TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    transcript_url TEXT,
    meeting_link TEXT,

    -- Participants and speakers
    participants JSONB DEFAULT '[]',  -- Array of email strings
    speakers JSONB DEFAULT '[]',       -- Array of speaker names

    -- AI-generated summaries
    summary TEXT,                      -- Short summary
    action_items TEXT,                 -- Formatted action items by person
    keywords TEXT[] DEFAULT '{}',      -- Array of keywords
    overview TEXT,                     -- Bullet gist/overview

    -- Source tracking
    source_type source_type NOT NULL DEFAULT 'FIREFLIES',
    raw_source_payload JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_calls_fireflies_id ON calls(fireflies_id);
CREATE INDEX idx_calls_client ON calls(client_id);
CREATE INDEX idx_calls_date ON calls(call_date DESC);
CREATE INDEX idx_calls_client_date ON calls(client_id, call_date DESC);

-- Full-text search on title and summary
CREATE INDEX idx_calls_search ON calls USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, '')));

-- Trigger for updated_at
CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
