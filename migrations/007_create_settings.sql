-- Migration 007: Create settings table (singleton)

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT '00000000-0000-0000-0000-000000000001'::UUID,

    -- Timezone
    timezone TEXT NOT NULL DEFAULT 'America/New_York',

    -- Work hours
    work_start_time TIME NOT NULL DEFAULT '09:00',
    work_end_time TIME NOT NULL DEFAULT '17:00',
    capacity_minutes_per_day INTEGER NOT NULL DEFAULT 360,  -- 6 hours default

    -- Timebox definitions
    morning_end TIME NOT NULL DEFAULT '12:00',
    afternoon_end TIME NOT NULL DEFAULT '17:00',

    -- Digest settings
    morning_digest_time TIME DEFAULT '06:00',
    evening_digest_time TIME DEFAULT '21:00',
    digest_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Ranking weights (should sum to approximately 100 for clarity)
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

    -- Client matching rules for calendar events
    -- Format: {
    --   "domains": [{"domain": "acme.com", "client_id": "uuid"}],
    --   "keywords": [{"keyword": "acme", "client_id": "uuid"}],
    --   "overrides": [{"gcal_event_id": "...", "client_id": "uuid"}]
    -- }
    client_matching_rules JSONB NOT NULL DEFAULT '{
        "domains": [],
        "keywords": [],
        "overrides": []
    }'::JSONB,

    -- Preferences
    default_task_duration_minutes INTEGER NOT NULL DEFAULT 30,
    auto_archive_completed_days INTEGER NOT NULL DEFAULT 7,
    show_completed_in_today BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure single row
    CONSTRAINT settings_singleton CHECK (id = '00000000-0000-0000-0000-000000000001'::UUID)
);

-- Insert default settings row
INSERT INTO settings (id) VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- Trigger for updated_at
CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
