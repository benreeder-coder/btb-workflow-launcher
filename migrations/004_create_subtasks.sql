-- Migration 004: Create subtasks table

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

-- Indexes
CREATE INDEX idx_subtasks_task ON subtasks(task_id);
CREATE INDEX idx_subtasks_task_status ON subtasks(task_id, status);
CREATE INDEX idx_subtasks_order ON subtasks(task_id, order_rank);

-- Trigger for updated_at
CREATE TRIGGER update_subtasks_updated_at
    BEFORE UPDATE ON subtasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to check if all subtasks are completed before allowing task completion
CREATE OR REPLACE FUNCTION check_subtasks_completed()
RETURNS TRIGGER AS $$
DECLARE
    incomplete_count INTEGER;
BEGIN
    -- Only check when status is being changed to COMPLETED
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
