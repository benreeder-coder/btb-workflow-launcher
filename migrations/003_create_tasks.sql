-- Migration 003: Create tasks table

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core fields
    title TEXT NOT NULL,
    description TEXT,

    -- Status & Priority
    status task_status NOT NULL DEFAULT 'NOT_STARTED',
    priority task_priority NOT NULL DEFAULT 'P2',

    -- Scheduling
    due_date DATE,
    due_time TIME,
    start_date DATE,
    snooze_until TIMESTAMPTZ,
    timebox_bucket timebox_bucket NOT NULL DEFAULT 'NONE',
    estimated_minutes INTEGER CHECK (estimated_minutes >= 0),
    pinned_today BOOLEAN NOT NULL DEFAULT FALSE,

    -- Tags and labels
    tags TEXT[] DEFAULT '{}',
    labels TEXT[] DEFAULT '{}',

    -- Blocking fields (for PENDING status)
    waiting_on TEXT,
    blocked_reason TEXT,

    -- Recurring task fields
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_rule TEXT,  -- RFC 5545 RRULE format
    recurrence_timezone TEXT DEFAULT 'America/New_York',
    recurrence_anchor_date DATE,
    next_occurrence_at TIMESTAMPTZ,
    recurrence_end_date DATE,
    recurrence_skip_weekends BOOLEAN NOT NULL DEFAULT FALSE,
    parent_recurring_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,

    -- Relations
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,

    -- Source tracking
    source_type source_type NOT NULL DEFAULT 'MANUAL',
    source_id TEXT,
    transcript_id TEXT,
    meeting_id TEXT,
    source_url TEXT,
    idempotency_key TEXT,
    raw_source_payload JSONB,
    schema_version INTEGER NOT NULL DEFAULT 1,

    -- Edit tracking
    last_edited_source source_type NOT NULL DEFAULT 'MANUAL',
    last_edited_at TIMESTAMPTZ,
    manually_edited BOOLEAN NOT NULL DEFAULT FALSE,
    manual_fields TEXT[] DEFAULT '{}',  -- Fields that were manually edited

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,

    -- Full-text search vector
    search_vector TSVECTOR
);

-- Unique constraints
CREATE UNIQUE INDEX idx_tasks_idempotency_key ON tasks(idempotency_key) WHERE idempotency_key IS NOT NULL;
-- Non-unique: multiple tasks can share same source (e.g., multiple action items from one call)
CREATE INDEX idx_tasks_source ON tasks(source_type, source_id) WHERE source_id IS NOT NULL;

-- Query indexes
CREATE INDEX idx_tasks_client_status ON tasks(client_id, status) WHERE archived_at IS NULL;
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE archived_at IS NULL;
CREATE INDEX idx_tasks_snooze_until ON tasks(snooze_until) WHERE snooze_until IS NOT NULL;
CREATE INDEX idx_tasks_completed_at ON tasks(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX idx_tasks_priority ON tasks(priority) WHERE archived_at IS NULL;
CREATE INDEX idx_tasks_next_occurrence ON tasks(next_occurrence_at) WHERE is_recurring = TRUE;
CREATE INDEX idx_tasks_status ON tasks(status) WHERE archived_at IS NULL;
CREATE INDEX idx_tasks_pinned ON tasks(pinned_today) WHERE pinned_today = TRUE AND archived_at IS NULL;
CREATE INDEX idx_tasks_timebox ON tasks(timebox_bucket) WHERE archived_at IS NULL AND timebox_bucket != 'NONE';
CREATE INDEX idx_tasks_archived ON tasks(archived_at) WHERE archived_at IS NOT NULL;
CREATE INDEX idx_tasks_parent_recurring ON tasks(parent_recurring_task_id) WHERE parent_recurring_task_id IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_tasks_search ON tasks USING GIN(search_vector);

-- Trigger for updated_at
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for search vector
CREATE OR REPLACE FUNCTION tasks_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.waiting_on, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.blocked_reason, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tasks_search_update
    BEFORE INSERT OR UPDATE OF title, description, waiting_on, blocked_reason ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION tasks_search_vector_update();
