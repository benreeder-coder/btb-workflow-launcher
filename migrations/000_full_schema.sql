-- Full Client Hub Schema
-- Run this entire file in Supabase SQL Editor to set up all tables at once
-- Alternatively, run migrations 001-007 in order

-- ============================================
-- MIGRATION 001: Enums and Functions
-- ============================================

-- Task status enum
CREATE TYPE task_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'PENDING', 'COMPLETED');

-- Priority enum
CREATE TYPE task_priority AS ENUM ('P0', 'P1', 'P2', 'P3');

-- Timebox enum
CREATE TYPE timebox_bucket AS ENUM ('MORNING', 'AFTERNOON', 'EVENING', 'NONE');

-- Source type enum
CREATE TYPE source_type AS ENUM ('MANUAL', 'N8N', 'FIREFLIES', 'CALENDAR');

-- Client status enum
CREATE TYPE client_status AS ENUM ('active', 'paused', 'churned', 'prospect');

-- Health status enum
CREATE TYPE health_status AS ENUM ('GREEN', 'YELLOW', 'RED');

-- Actor type for activity log
CREATE TYPE actor_type AS ENUM ('MANUAL', 'N8N', 'SYSTEM');

-- Action type for activity log
CREATE TYPE action_type AS ENUM (
    'CREATED', 'UPDATED', 'DELETED', 'ARCHIVED', 'RESTORED',
    'STATUS_CHANGED', 'PRIORITY_CHANGED', 'DUE_DATE_CHANGED',
    'INGESTED', 'DEDUPE_MERGE', 'RECURRENCE_GENERATED',
    'SUBTASK_ADDED', 'SUBTASK_COMPLETED', 'ASSIGNED', 'COMPLETED'
);

-- Entity type for activity log
CREATE TYPE entity_type AS ENUM ('TASK', 'SUBTASK', 'CLIENT', 'SETTINGS', 'CALENDAR_EVENT');

-- Utility function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- MIGRATION 002: Clients Table
-- ============================================

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

CREATE INDEX idx_clients_status ON clients(status) WHERE archived_at IS NULL;
CREATE INDEX idx_clients_name ON clients(LOWER(name));
CREATE INDEX idx_clients_archived ON clients(archived_at) WHERE archived_at IS NOT NULL;

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE clients ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(notes, ''))) STORED;

CREATE INDEX idx_clients_search ON clients USING GIN(search_vector);


-- ============================================
-- MIGRATION 003: Tasks Table
-- ============================================

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'NOT_STARTED',
    priority task_priority NOT NULL DEFAULT 'P2',
    due_date DATE,
    due_time TIME,
    start_date DATE,
    snooze_until TIMESTAMPTZ,
    timebox_bucket timebox_bucket NOT NULL DEFAULT 'NONE',
    estimated_minutes INTEGER CHECK (estimated_minutes >= 0),
    pinned_today BOOLEAN NOT NULL DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    labels TEXT[] DEFAULT '{}',
    waiting_on TEXT,
    blocked_reason TEXT,
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_rule TEXT,
    recurrence_timezone TEXT DEFAULT 'America/New_York',
    recurrence_anchor_date DATE,
    next_occurrence_at TIMESTAMPTZ,
    recurrence_end_date DATE,
    recurrence_skip_weekends BOOLEAN NOT NULL DEFAULT FALSE,
    parent_recurring_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    source_type source_type NOT NULL DEFAULT 'MANUAL',
    source_id TEXT,
    transcript_id TEXT,
    meeting_id TEXT,
    source_url TEXT,
    idempotency_key TEXT,
    raw_source_payload JSONB,
    schema_version INTEGER NOT NULL DEFAULT 1,
    last_edited_source source_type NOT NULL DEFAULT 'MANUAL',
    last_edited_at TIMESTAMPTZ,
    manually_edited BOOLEAN NOT NULL DEFAULT FALSE,
    manual_fields TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    search_vector TSVECTOR
);

CREATE UNIQUE INDEX idx_tasks_idempotency_key ON tasks(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX idx_tasks_source ON tasks(source_type, source_id) WHERE source_id IS NOT NULL;
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
CREATE INDEX idx_tasks_search ON tasks USING GIN(search_vector);

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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


-- ============================================
-- MIGRATION 004: Subtasks Table
-- ============================================

CREATE TABLE subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status task_status NOT NULL DEFAULT 'NOT_STARTED',
    priority task_priority,
    due_date DATE,
    order_rank INTEGER NOT NULL DEFAULT 0,
    waiting_on TEXT,
    blocked_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_subtasks_task ON subtasks(task_id);
CREATE INDEX idx_subtasks_task_status ON subtasks(task_id, status);
CREATE INDEX idx_subtasks_order ON subtasks(task_id, order_rank);

CREATE TRIGGER update_subtasks_updated_at
    BEFORE UPDATE ON subtasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION check_subtasks_completed()
RETURNS TRIGGER AS $$
DECLARE
    incomplete_count INTEGER;
BEGIN
    IF NEW.status = 'COMPLETED' AND (OLD.status IS NULL OR OLD.status != 'COMPLETED') THEN
        SELECT COUNT(*) INTO incomplete_count
        FROM subtasks
        WHERE task_id = NEW.id AND status != 'COMPLETED';

        IF incomplete_count > 0 THEN
            RAISE EXCEPTION 'Cannot complete task with % incomplete subtask(s)', incomplete_count;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_subtask_completion
    BEFORE UPDATE OF status ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION check_subtasks_completed();


-- ============================================
-- MIGRATION 005: Activity Log Table
-- ============================================

CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    action_type action_type NOT NULL,
    field_name TEXT,
    old_value JSONB,
    new_value JSONB,
    changes JSONB,
    actor actor_type NOT NULL DEFAULT 'MANUAL',
    source_info JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_created ON activity_log(created_at DESC);
CREATE INDEX idx_activity_action ON activity_log(action_type);
CREATE INDEX idx_activity_actor ON activity_log(actor);
CREATE INDEX idx_activity_entity_created ON activity_log(entity_type, entity_id, created_at DESC);


-- ============================================
-- MIGRATION 006: Calendar Events Table
-- ============================================

CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gcal_event_id TEXT UNIQUE NOT NULL,
    calendar_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    meeting_link TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN NOT NULL DEFAULT FALSE,
    timezone TEXT DEFAULT 'America/New_York',
    attendees JSONB DEFAULT '[]',
    organizer_email TEXT,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    match_confidence INTEGER CHECK (match_confidence >= 0 AND match_confidence <= 100),
    match_method TEXT,
    etag TEXT,
    raw JSONB,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calendar_gcal_id ON calendar_events(gcal_event_id);
CREATE INDEX idx_calendar_start ON calendar_events(start_time);
CREATE INDEX idx_calendar_end ON calendar_events(end_time);
CREATE INDEX idx_calendar_client ON calendar_events(client_id);
CREATE INDEX idx_calendar_date_range ON calendar_events(start_time, end_time);
CREATE INDEX idx_calendar_date ON calendar_events(DATE(start_time AT TIME ZONE 'America/New_York'));

CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- MIGRATION 007: Settings Table (Singleton)
-- ============================================

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT '00000000-0000-0000-0000-000000000001'::UUID,
    timezone TEXT NOT NULL DEFAULT 'America/New_York',
    work_start_time TIME NOT NULL DEFAULT '09:00',
    work_end_time TIME NOT NULL DEFAULT '17:00',
    capacity_minutes_per_day INTEGER NOT NULL DEFAULT 360,
    morning_end TIME NOT NULL DEFAULT '12:00',
    afternoon_end TIME NOT NULL DEFAULT '17:00',
    morning_digest_time TIME DEFAULT '06:00',
    evening_digest_time TIME DEFAULT '21:00',
    digest_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ranking_weights JSONB NOT NULL DEFAULT '{
        "overdue": 100,
        "due_today": 60,
        "priority_p0": 50,
        "priority_p1": 30,
        "priority_p2": 15,
        "priority_p3": 0,
        "in_progress": 10,
        "pending": -10,
        "client_weight_multiplier": 1
    }'::JSONB,
    client_matching_rules JSONB NOT NULL DEFAULT '{
        "domains": [],
        "keywords": [],
        "overrides": []
    }'::JSONB,
    default_task_duration_minutes INTEGER NOT NULL DEFAULT 30,
    auto_archive_completed_days INTEGER NOT NULL DEFAULT 7,
    show_completed_in_today BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT settings_singleton CHECK (id = '00000000-0000-0000-0000-000000000001'::UUID)
);

INSERT INTO settings (id) VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- SETUP COMPLETE
-- ============================================
-- Tables created:
--   1. clients
--   2. tasks
--   3. subtasks
--   4. activity_log
--   5. calendar_events
--   6. settings
--
-- Next steps:
-- 1. Add your SUPABASE_URL and SUPABASE_KEY to .env
-- 2. Run the Python application
