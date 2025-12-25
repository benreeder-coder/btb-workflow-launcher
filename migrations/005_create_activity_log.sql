-- Migration 005: Create activity_log table

CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What changed
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    action_type action_type NOT NULL,

    -- Change details
    field_name TEXT,
    old_value JSONB,
    new_value JSONB,
    changes JSONB,  -- For multi-field updates

    -- Context
    actor actor_type NOT NULL DEFAULT 'MANUAL',
    source_info JSONB,  -- Additional context like workflow_id, run_id

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for querying activity
CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_created ON activity_log(created_at DESC);
CREATE INDEX idx_activity_action ON activity_log(action_type);
CREATE INDEX idx_activity_actor ON activity_log(actor);

-- Composite index for common queries
CREATE INDEX idx_activity_entity_created ON activity_log(entity_type, entity_id, created_at DESC);
