-- Migration 006: Create calendar_events table

CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Google Calendar identifiers
    gcal_event_id TEXT UNIQUE NOT NULL,
    calendar_id TEXT,

    -- Event details
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    meeting_link TEXT,

    -- Timing
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN NOT NULL DEFAULT FALSE,
    timezone TEXT DEFAULT 'America/New_York',

    -- Attendees stored as JSON array
    -- Format: [{"email": "...", "name": "...", "response_status": "..."}]
    attendees JSONB DEFAULT '[]',
    organizer_email TEXT,

    -- Client mapping
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    match_confidence INTEGER CHECK (match_confidence >= 0 AND match_confidence <= 100),
    match_method TEXT,  -- 'domain', 'keyword', 'override', 'manual'

    -- Sync metadata
    etag TEXT,
    raw JSONB,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_calendar_gcal_id ON calendar_events(gcal_event_id);
CREATE INDEX idx_calendar_start ON calendar_events(start_time);
CREATE INDEX idx_calendar_end ON calendar_events(end_time);
CREATE INDEX idx_calendar_client ON calendar_events(client_id);
CREATE INDEX idx_calendar_date_range ON calendar_events(start_time, end_time);

-- Index for finding events by date (for Today view)
CREATE INDEX idx_calendar_date ON calendar_events(DATE(start_time AT TIME ZONE 'America/New_York'));

-- Trigger for updated_at
CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
