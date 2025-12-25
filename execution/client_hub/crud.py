"""
CRUD operations for Client Hub.

This module provides database operations for:
- Clients
- Tasks and subtasks
- Calendar events
- Activity logging
- Settings
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import json

from supabase import Client as SupabaseClient

from .models import (
    # Enums
    TaskStatus, TaskPriority, TimeboxBucket, SourceType,
    EntityType, ActionType, ActorType,
    # Client models
    Client, ClientCreate, ClientUpdate, ClientWithCounts,
    # Task models
    Task, TaskCreate, TaskUpdate, TaskWithSubtasks,
    # Subtask models
    Subtask, SubtaskCreate, SubtaskUpdate,
    # Activity log
    ActivityLogCreate,
    # Calendar
    CalendarEvent, CalendarEventCreate,
    # Settings
    Settings, SettingsUpdate,
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def _serialize_for_db(data: dict) -> dict:
    """Convert Python types to JSON-serializable types for Supabase."""
    result = {}
    for key, value in data.items():
        if value is None:
            result[key] = None
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
        elif isinstance(value, UUID):
            result[key] = str(value)
        elif hasattr(value, 'value'):  # Enum
            result[key] = value.value
        elif isinstance(value, list):
            result[key] = [
                _serialize_for_db(v) if isinstance(v, dict) else
                str(v) if isinstance(v, UUID) else v
                for v in value
            ]
        elif isinstance(value, dict):
            result[key] = _serialize_for_db(value)
        else:
            result[key] = value
    return result


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try ISO format
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass
    return None


def _parse_date(value: Any) -> Optional[date]:
    """Parse date from various formats."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            pass
    return None


# ============================================
# ACTIVITY LOGGING
# ============================================

async def log_activity(
    supabase: SupabaseClient,
    entity_type: EntityType,
    entity_id: UUID,
    action_type: ActionType,
    actor: ActorType = ActorType.MANUAL,
    field_name: Optional[str] = None,
    old_value: Any = None,
    new_value: Any = None,
    changes: Optional[Dict[str, Any]] = None,
    source_info: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an activity for audit trail."""
    data = {
        "entity_type": entity_type.value,
        "entity_id": str(entity_id),
        "action_type": action_type.value,
        "actor": actor.value,
        "field_name": field_name,
        "old_value": json.dumps(old_value) if old_value is not None else None,
        "new_value": json.dumps(new_value) if new_value is not None else None,
        "changes": changes,
        "source_info": source_info,
    }
    supabase.table("activity_log").insert(data).execute()


# ============================================
# CLIENT CRUD
# ============================================

def get_clients(
    supabase: SupabaseClient,
    include_archived: bool = False,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ClientWithCounts]:
    """Get all clients with task counts."""
    query = supabase.table("clients").select("*")

    if not include_archived:
        query = query.is_("archived_at", "null")

    if status:
        query = query.eq("status", status)

    if search:
        query = query.ilike("name", f"%{search}%")

    query = query.order("name").range(offset, offset + limit - 1)
    result = query.execute()

    clients = []
    for row in result.data:
        # Get task counts for each client
        counts = supabase.table("tasks").select(
            "id, status, due_date",
            count="exact"
        ).eq("client_id", row["id"]).is_("archived_at", "null").execute()

        total = len(counts.data)
        open_tasks = sum(1 for t in counts.data if t["status"] != "COMPLETED")
        overdue = sum(
            1 for t in counts.data
            if t["due_date"] and _parse_date(t["due_date"]) < date.today()
            and t["status"] != "COMPLETED"
        )
        pending = sum(1 for t in counts.data if t["status"] == "PENDING")

        client_data = {
            **row,
            "total_tasks": total,
            "open_tasks": open_tasks,
            "overdue_tasks": overdue,
            "pending_tasks": pending,
        }
        clients.append(ClientWithCounts(**client_data))

    return clients


def get_client(supabase: SupabaseClient, client_id: UUID) -> Optional[Client]:
    """Get a single client by ID."""
    result = supabase.table("clients").select("*").eq("id", str(client_id)).execute()
    if result.data:
        return Client(**result.data[0])
    return None


def create_client(
    supabase: SupabaseClient,
    client: ClientCreate,
    actor: ActorType = ActorType.MANUAL,
) -> Client:
    """Create a new client."""
    data = _serialize_for_db(client.model_dump(exclude_unset=True))
    result = supabase.table("clients").insert(data).execute()
    created = Client(**result.data[0])

    # Log activity
    log_activity(
        supabase,
        EntityType.CLIENT,
        created.id,
        ActionType.CREATED,
        actor=actor,
        new_value=data,
    )

    return created


def update_client(
    supabase: SupabaseClient,
    client_id: UUID,
    updates: ClientUpdate,
    actor: ActorType = ActorType.MANUAL,
) -> Optional[Client]:
    """Update a client."""
    # Get current state
    current = get_client(supabase, client_id)
    if not current:
        return None

    data = _serialize_for_db(updates.model_dump(exclude_unset=True, exclude_none=True))
    if not data:
        return current

    result = supabase.table("clients").update(data).eq("id", str(client_id)).execute()
    updated = Client(**result.data[0])

    # Log activity
    log_activity(
        supabase,
        EntityType.CLIENT,
        client_id,
        ActionType.UPDATED,
        actor=actor,
        changes=data,
    )

    return updated


def archive_client(
    supabase: SupabaseClient,
    client_id: UUID,
    actor: ActorType = ActorType.MANUAL,
) -> Optional[Client]:
    """Archive a client (soft delete)."""
    result = supabase.table("clients").update({
        "archived_at": datetime.utcnow().isoformat()
    }).eq("id", str(client_id)).execute()

    if result.data:
        log_activity(
            supabase,
            EntityType.CLIENT,
            client_id,
            ActionType.ARCHIVED,
            actor=actor,
        )
        return Client(**result.data[0])
    return None


# ============================================
# TASK CRUD
# ============================================

def get_tasks(
    supabase: SupabaseClient,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    client_id: Optional[UUID] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    include_archived: bool = False,
    include_snoozed: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Task]:
    """Get tasks with filters."""
    query = supabase.table("tasks").select("*")

    if not include_archived:
        query = query.is_("archived_at", "null")

    if not include_snoozed:
        query = query.or_(
            f"snooze_until.is.null,snooze_until.lte.{datetime.utcnow().isoformat()}"
        )

    if status:
        query = query.eq("status", status.value)

    if priority:
        query = query.eq("priority", priority.value)

    if client_id:
        query = query.eq("client_id", str(client_id))

    if due_before:
        query = query.lte("due_date", due_before.isoformat())

    if due_after:
        query = query.gte("due_date", due_after.isoformat())

    if search:
        # Use full-text search
        query = query.text_search("search_vector", search)

    query = query.order("due_date", nullsfirst=False).range(offset, offset + limit - 1)
    result = query.execute()

    return [Task(**row) for row in result.data]


def get_task(supabase: SupabaseClient, task_id: UUID) -> Optional[TaskWithSubtasks]:
    """Get a single task with subtasks."""
    result = supabase.table("tasks").select("*").eq("id", str(task_id)).execute()
    if not result.data:
        return None

    task_data = result.data[0]

    # Get subtasks
    subtasks_result = supabase.table("subtasks").select("*").eq(
        "task_id", str(task_id)
    ).order("order_rank").execute()
    subtasks = [Subtask(**s) for s in subtasks_result.data]

    # Get client if exists
    client = None
    if task_data.get("client_id"):
        client = get_client(supabase, UUID(task_data["client_id"]))

    return TaskWithSubtasks(**task_data, subtasks=subtasks, client=client)


def create_task(
    supabase: SupabaseClient,
    task: TaskCreate,
    actor: ActorType = ActorType.MANUAL,
) -> TaskWithSubtasks:
    """Create a new task with optional subtasks."""
    # Extract subtasks
    subtasks_data = task.subtasks
    task_data = _serialize_for_db(task.model_dump(exclude={"subtasks"}, exclude_unset=True))

    # Set manual edit tracking
    if actor == ActorType.MANUAL:
        task_data["last_edited_source"] = "MANUAL"
        task_data["last_edited_at"] = datetime.utcnow().isoformat()

    result = supabase.table("tasks").insert(task_data).execute()
    created_task = result.data[0]
    task_id = created_task["id"]

    # Create subtasks
    subtasks = []
    for i, subtask in enumerate(subtasks_data):
        subtask_data = _serialize_for_db(subtask.model_dump(exclude_unset=True))
        subtask_data["task_id"] = task_id
        subtask_data["order_rank"] = subtask.order_rank or i
        sub_result = supabase.table("subtasks").insert(subtask_data).execute()
        subtasks.append(Subtask(**sub_result.data[0]))

    # Log activity
    log_activity(
        supabase,
        EntityType.TASK,
        UUID(task_id),
        ActionType.CREATED,
        actor=actor,
        new_value=task_data,
    )

    # Get client if exists
    client = None
    if created_task.get("client_id"):
        client = get_client(supabase, UUID(created_task["client_id"]))

    return TaskWithSubtasks(**created_task, subtasks=subtasks, client=client)


def update_task(
    supabase: SupabaseClient,
    task_id: UUID,
    updates: TaskUpdate,
    actor: ActorType = ActorType.MANUAL,
    respect_manual_protection: bool = True,
) -> Optional[TaskWithSubtasks]:
    """Update a task."""
    current = get_task(supabase, task_id)
    if not current:
        return None

    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)

    # Manual edit protection for n8n updates
    if respect_manual_protection and actor == ActorType.N8N and current.manually_edited:
        protected_fields = current.manual_fields
        update_data = {k: v for k, v in update_data.items() if k not in protected_fields}

    if not update_data:
        return current

    data = _serialize_for_db(update_data)

    # Track manual edits
    if actor == ActorType.MANUAL:
        data["last_edited_source"] = "MANUAL"
        data["last_edited_at"] = datetime.utcnow().isoformat()
        data["manually_edited"] = True
        # Add edited fields to manual_fields
        new_manual_fields = list(set(current.manual_fields + list(update_data.keys())))
        data["manual_fields"] = new_manual_fields

    # Handle completion
    if updates.status == TaskStatus.COMPLETED and current.status != TaskStatus.COMPLETED:
        data["completed_at"] = datetime.utcnow().isoformat()

    result = supabase.table("tasks").update(data).eq("id", str(task_id)).execute()

    # Log specific field changes
    for field, new_value in update_data.items():
        old_value = getattr(current, field, None)
        if old_value != new_value:
            action = ActionType.UPDATED
            if field == "status":
                action = ActionType.STATUS_CHANGED
            elif field == "priority":
                action = ActionType.PRIORITY_CHANGED
            elif field == "due_date":
                action = ActionType.DUE_DATE_CHANGED

            log_activity(
                supabase,
                EntityType.TASK,
                task_id,
                action,
                actor=actor,
                field_name=field,
                old_value=str(old_value) if old_value else None,
                new_value=str(new_value) if new_value else None,
            )

    return get_task(supabase, task_id)


def complete_task(
    supabase: SupabaseClient,
    task_id: UUID,
    actor: ActorType = ActorType.MANUAL,
) -> Tuple[Optional[TaskWithSubtasks], Optional[str]]:
    """
    Complete a task if all subtasks are completed.
    Returns (task, error_message).
    """
    task = get_task(supabase, task_id)
    if not task:
        return None, "Task not found"

    # Check subtasks
    incomplete = [s for s in task.subtasks if s.status != TaskStatus.COMPLETED]
    if incomplete:
        return None, f"Cannot complete task with {len(incomplete)} incomplete subtask(s)"

    return update_task(
        supabase,
        task_id,
        TaskUpdate(status=TaskStatus.COMPLETED),
        actor=actor,
    ), None


def archive_task(
    supabase: SupabaseClient,
    task_id: UUID,
    actor: ActorType = ActorType.MANUAL,
) -> Optional[TaskWithSubtasks]:
    """Archive a task (soft delete)."""
    result = supabase.table("tasks").update({
        "archived_at": datetime.utcnow().isoformat()
    }).eq("id", str(task_id)).execute()

    if result.data:
        log_activity(
            supabase,
            EntityType.TASK,
            task_id,
            ActionType.ARCHIVED,
            actor=actor,
        )
        return get_task(supabase, task_id)
    return None


def pin_task(
    supabase: SupabaseClient,
    task_id: UUID,
    pinned: bool = True,
) -> Optional[TaskWithSubtasks]:
    """Toggle pin status for a task."""
    supabase.table("tasks").update({
        "pinned_today": pinned
    }).eq("id", str(task_id)).execute()
    return get_task(supabase, task_id)


def snooze_task(
    supabase: SupabaseClient,
    task_id: UUID,
    until: datetime,
) -> Optional[TaskWithSubtasks]:
    """Snooze a task until a specific time."""
    supabase.table("tasks").update({
        "snooze_until": until.isoformat()
    }).eq("id", str(task_id)).execute()
    return get_task(supabase, task_id)


# ============================================
# SUBTASK CRUD
# ============================================

def get_subtasks(
    supabase: SupabaseClient,
    task_id: UUID,
) -> List[Subtask]:
    """Get all subtasks for a task."""
    result = supabase.table("subtasks").select("*").eq(
        "task_id", str(task_id)
    ).order("order_rank").execute()
    return [Subtask(**s) for s in result.data]


def create_subtask(
    supabase: SupabaseClient,
    task_id: UUID,
    subtask: SubtaskCreate,
    actor: ActorType = ActorType.MANUAL,
) -> Subtask:
    """Create a new subtask."""
    # Get max order_rank
    existing = get_subtasks(supabase, task_id)
    max_rank = max((s.order_rank for s in existing), default=-1)

    data = _serialize_for_db(subtask.model_dump(exclude_unset=True))
    data["task_id"] = str(task_id)
    data["order_rank"] = subtask.order_rank or (max_rank + 1)

    result = supabase.table("subtasks").insert(data).execute()
    created = Subtask(**result.data[0])

    log_activity(
        supabase,
        EntityType.TASK,
        task_id,
        ActionType.SUBTASK_ADDED,
        actor=actor,
        new_value={"subtask_id": str(created.id), "title": created.title},
    )

    return created


def update_subtask(
    supabase: SupabaseClient,
    subtask_id: UUID,
    updates: SubtaskUpdate,
    actor: ActorType = ActorType.MANUAL,
) -> Optional[Subtask]:
    """Update a subtask."""
    data = _serialize_for_db(updates.model_dump(exclude_unset=True, exclude_none=True))

    # Handle completion
    if updates.status == TaskStatus.COMPLETED:
        data["completed_at"] = datetime.utcnow().isoformat()

    result = supabase.table("subtasks").update(data).eq("id", str(subtask_id)).execute()

    if result.data:
        subtask = Subtask(**result.data[0])
        if updates.status == TaskStatus.COMPLETED:
            log_activity(
                supabase,
                EntityType.TASK,
                subtask.task_id,
                ActionType.SUBTASK_COMPLETED,
                actor=actor,
                new_value={"subtask_id": str(subtask_id)},
            )
        return subtask
    return None


def delete_subtask(
    supabase: SupabaseClient,
    subtask_id: UUID,
) -> bool:
    """Delete a subtask."""
    result = supabase.table("subtasks").delete().eq("id", str(subtask_id)).execute()
    return bool(result.data)


def reorder_subtasks(
    supabase: SupabaseClient,
    task_id: UUID,
    subtask_ids: List[UUID],
) -> List[Subtask]:
    """Reorder subtasks by updating their order_rank."""
    for i, subtask_id in enumerate(subtask_ids):
        supabase.table("subtasks").update({
            "order_rank": i
        }).eq("id", str(subtask_id)).execute()

    return get_subtasks(supabase, task_id)


# ============================================
# CALENDAR CRUD
# ============================================

def get_calendar_events(
    supabase: SupabaseClient,
    start_date: date,
    end_date: date,
    client_id: Optional[UUID] = None,
) -> List[CalendarEvent]:
    """Get calendar events in a date range."""
    query = supabase.table("calendar_events").select("*").gte(
        "start_time", f"{start_date}T00:00:00"
    ).lte("end_time", f"{end_date}T23:59:59")

    if client_id:
        query = query.eq("client_id", str(client_id))

    result = query.order("start_time").execute()

    events = []
    for row in result.data:
        client = None
        if row.get("client_id"):
            client = get_client(supabase, UUID(row["client_id"]))
        events.append(CalendarEvent(**row, client=client))

    return events


def upsert_calendar_event(
    supabase: SupabaseClient,
    event: CalendarEventCreate,
) -> CalendarEvent:
    """Upsert a calendar event by gcal_event_id."""
    data = _serialize_for_db(event.model_dump(exclude_unset=True))
    data["synced_at"] = datetime.utcnow().isoformat()

    # Convert attendees to JSON
    if "attendees" in data:
        data["attendees"] = [a if isinstance(a, dict) else a.model_dump() for a in data["attendees"]]

    result = supabase.table("calendar_events").upsert(
        data, on_conflict="gcal_event_id"
    ).execute()

    return CalendarEvent(**result.data[0])


def map_event_to_client(
    supabase: SupabaseClient,
    event_id: UUID,
    client_id: UUID,
    match_confidence: int = 100,
) -> Optional[CalendarEvent]:
    """Manually map a calendar event to a client."""
    result = supabase.table("calendar_events").update({
        "client_id": str(client_id),
        "match_confidence": match_confidence,
        "match_method": "manual",
    }).eq("id", str(event_id)).execute()

    if result.data:
        return CalendarEvent(**result.data[0])
    return None


# ============================================
# SETTINGS CRUD
# ============================================

SETTINGS_ID = "00000000-0000-0000-0000-000000000001"


def get_settings(supabase: SupabaseClient) -> Settings:
    """Get settings (singleton)."""
    try:
        result = supabase.table("settings").select("*").eq("id", SETTINGS_ID).execute()
        if result.data:
            data = result.data[0]
            # Parse JSON fields
            if isinstance(data.get("ranking_weights"), str):
                data["ranking_weights"] = json.loads(data["ranking_weights"])
            if isinstance(data.get("client_matching_rules"), str):
                data["client_matching_rules"] = json.loads(data["client_matching_rules"])

            # Parse time fields from string format
            time_fields = ['work_start_time', 'work_end_time', 'morning_end', 'afternoon_end',
                          'morning_digest_time', 'evening_digest_time']
            for field in time_fields:
                if field in data and data[field] is not None:
                    if isinstance(data[field], str):
                        # Parse time string like "09:00:00" to time object
                        try:
                            data[field] = datetime.strptime(data[field], "%H:%M:%S").time()
                        except ValueError:
                            try:
                                data[field] = datetime.strptime(data[field], "%H:%M").time()
                            except ValueError:
                                data[field] = None

            return Settings(**data)

        # Create default if not exists
        supabase.table("settings").insert({"id": SETTINGS_ID}).execute()
        return Settings()
    except Exception as e:
        # If anything fails, return defaults to avoid blocking the app
        import logging
        logging.warning(f"Failed to get settings: {e}, using defaults")
        return Settings()


def update_settings(
    supabase: SupabaseClient,
    updates: SettingsUpdate,
) -> Settings:
    """Update settings."""
    data = updates.model_dump(exclude_unset=True, exclude_none=True)

    # Serialize nested models
    if "ranking_weights" in data and data["ranking_weights"]:
        data["ranking_weights"] = data["ranking_weights"].model_dump() if hasattr(data["ranking_weights"], 'model_dump') else data["ranking_weights"]
    if "client_matching_rules" in data and data["client_matching_rules"]:
        data["client_matching_rules"] = data["client_matching_rules"].model_dump() if hasattr(data["client_matching_rules"], 'model_dump') else data["client_matching_rules"]

    data = _serialize_for_db(data)

    supabase.table("settings").update(data).eq("id", SETTINGS_ID).execute()
    return get_settings(supabase)


# ============================================
# VIEW-SPECIFIC QUERIES
# ============================================

def get_today_tasks(
    supabase: SupabaseClient,
    today: Optional[date] = None,
) -> List[TaskWithSubtasks]:
    """Get tasks for Today view."""
    if today is None:
        today = date.today()

    # Get tasks that are:
    # - Due today or overdue
    # - Start date is today
    # - Pinned
    # - Not snoozed (or snooze expired)
    # - Not completed or archived

    query = supabase.table("tasks").select("*").or_(
        f"due_date.eq.{today.isoformat()},"
        f"due_date.lt.{today.isoformat()},"
        f"start_date.eq.{today.isoformat()},"
        "pinned_today.eq.true"
    ).neq("status", "COMPLETED").is_("archived_at", "null")

    result = query.execute()

    tasks = []
    for row in result.data:
        # Filter out snoozed tasks
        if row.get("snooze_until"):
            snooze_until = _parse_datetime(row["snooze_until"])
            if snooze_until and snooze_until > datetime.utcnow():
                continue

        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def get_inbox_tasks(supabase: SupabaseClient) -> List[TaskWithSubtasks]:
    """Get tasks needing triage (missing client, due date, or priority)."""
    # Tasks that need triage:
    # - Missing client_id
    # - Missing due_date
    # - Priority is default (P2) and was never manually set

    query = supabase.table("tasks").select("*").or_(
        "client_id.is.null,"
        "due_date.is.null"
    ).neq("status", "COMPLETED").is_("archived_at", "null")

    result = query.execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def get_pending_tasks(supabase: SupabaseClient) -> List[TaskWithSubtasks]:
    """Get tasks with PENDING status."""
    query = supabase.table("tasks").select("*").eq(
        "status", "PENDING"
    ).is_("archived_at", "null")

    result = query.execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def get_overdue_tasks(
    supabase: SupabaseClient,
    today: Optional[date] = None,
) -> List[TaskWithSubtasks]:
    """Get overdue tasks."""
    if today is None:
        today = date.today()

    query = supabase.table("tasks").select("*").lt(
        "due_date", today.isoformat()
    ).neq("status", "COMPLETED").is_("archived_at", "null")

    result = query.execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def get_upcoming_tasks(
    supabase: SupabaseClient,
    days: int = 7,
    today: Optional[date] = None,
) -> List[TaskWithSubtasks]:
    """Get tasks due in the next N days."""
    if today is None:
        today = date.today()

    end_date = today + timedelta(days=days)

    query = supabase.table("tasks").select("*").gte(
        "due_date", today.isoformat()
    ).lte("due_date", end_date.isoformat()).neq(
        "status", "COMPLETED"
    ).is_("archived_at", "null")

    result = query.execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def get_completed_tasks(
    supabase: SupabaseClient,
    days: int = 7,
) -> List[TaskWithSubtasks]:
    """Get recently completed tasks."""
    since = datetime.utcnow() - timedelta(days=days)

    query = supabase.table("tasks").select("*").eq(
        "status", "COMPLETED"
    ).gte("completed_at", since.isoformat()).is_("archived_at", "null")

    result = query.order("completed_at", desc=True).execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def search_tasks(
    supabase: SupabaseClient,
    query: str,
    limit: int = 20,
) -> List[TaskWithSubtasks]:
    """Full-text search across tasks."""
    result = supabase.table("tasks").select("*").text_search(
        "search_vector", query
    ).is_("archived_at", "null").limit(limit).execute()

    tasks = []
    for row in result.data:
        task = get_task(supabase, UUID(row["id"]))
        if task:
            tasks.append(task)

    return tasks


def search_clients(
    supabase: SupabaseClient,
    query: str,
    limit: int = 10,
) -> List[Client]:
    """Full-text search across clients."""
    result = supabase.table("clients").select("*").text_search(
        "search_vector", query
    ).is_("archived_at", "null").limit(limit).execute()

    return [Client(**row) for row in result.data]
