-- Migration 001: Create enums and utility functions
-- Run this first in Supabase SQL Editor

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
