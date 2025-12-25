"""
Client Hub API Router

REST endpoints for:
- Tasks and subtasks
- Clients
- Calendar events
- Settings
- View-specific queries (Today, Inbox, Pending, etc.)
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from supabase_client import get_supabase, SupabaseClientError
from . import crud
from .models import (
    # Enums
    TaskStatus, TaskPriority, TimeboxBucket, ActorType,
    # Client models
    Client, ClientCreate, ClientUpdate, ClientWithCounts,
    # Task models
    Task, TaskCreate, TaskUpdate, TaskWithSubtasks,
    # Subtask models
    Subtask, SubtaskCreate, SubtaskUpdate,
    # Calendar
    CalendarEvent,
    # Settings
    Settings, SettingsUpdate,
    # View responses
    TodayViewResponse, InboxViewResponse, PendingViewResponse,
    UpcomingViewResponse, CompletedViewResponse, SearchResponse,
)
from .ranking import rank_tasks

# Create router with prefix
router = APIRouter(prefix="/api/hub", tags=["Client Hub"])


def get_db():
    """Dependency to get Supabase client."""
    try:
        return get_supabase()
    except SupabaseClientError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ============================================
# CLIENT ENDPOINTS
# ============================================

@router.get("/clients", response_model=List[ClientWithCounts])
def list_clients(
    include_archived: bool = False,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db=Depends(get_db),
):
    """List all clients with task counts."""
    return crud.get_clients(
        db,
        include_archived=include_archived,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/clients/{client_id}", response_model=Client)
def get_client(client_id: UUID, db=Depends(get_db)):
    """Get a single client by ID."""
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/clients", response_model=Client, status_code=201)
def create_client(client: ClientCreate, db=Depends(get_db)):
    """Create a new client."""
    return crud.create_client(db, client)


@router.put("/clients/{client_id}", response_model=Client)
def update_client(client_id: UUID, updates: ClientUpdate, db=Depends(get_db)):
    """Update a client."""
    client = crud.update_client(db, client_id, updates)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/clients/{client_id}", response_model=Client)
def archive_client(client_id: UUID, db=Depends(get_db)):
    """Archive a client (soft delete)."""
    client = crud.archive_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/clients/{client_id}/tasks", response_model=List[TaskWithSubtasks])
def get_client_tasks(
    client_id: UUID,
    status: Optional[TaskStatus] = None,
    include_archived: bool = False,
    db=Depends(get_db),
):
    """Get all tasks for a specific client."""
    return crud.get_tasks(
        db,
        client_id=client_id,
        status=status,
        include_archived=include_archived,
    )


# ============================================
# TASK ENDPOINTS
# ============================================

@router.get("/tasks", response_model=List[Task])
def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    client_id: Optional[UUID] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    include_archived: bool = False,
    include_snoozed: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db=Depends(get_db),
):
    """List tasks with filters."""
    return crud.get_tasks(
        db,
        status=status,
        priority=priority,
        client_id=client_id,
        due_before=due_before,
        due_after=due_after,
        include_archived=include_archived,
        include_snoozed=include_snoozed,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/tasks/{task_id}", response_model=TaskWithSubtasks)
def get_task(task_id: UUID, db=Depends(get_db)):
    """Get a single task with subtasks."""
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=TaskWithSubtasks, status_code=201)
def create_task(task: TaskCreate, db=Depends(get_db)):
    """Create a new task with optional subtasks."""
    return crud.create_task(db, task)


@router.put("/tasks/{task_id}", response_model=TaskWithSubtasks)
def update_task(task_id: UUID, updates: TaskUpdate, db=Depends(get_db)):
    """Update a task."""
    task = crud.update_task(db, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskWithSubtasks)
def change_task_status(task_id: UUID, status: TaskStatus, db=Depends(get_db)):
    """Change task status."""
    task = crud.update_task(db, task_id, TaskUpdate(status=status))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/complete", response_model=TaskWithSubtasks)
def complete_task(task_id: UUID, db=Depends(get_db)):
    """Complete a task (validates all subtasks are complete)."""
    task, error = crud.complete_task(db, task_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return task


@router.delete("/tasks/{task_id}", response_model=TaskWithSubtasks)
def archive_task(task_id: UUID, db=Depends(get_db)):
    """Archive a task (soft delete)."""
    task = crud.archive_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/pin", response_model=TaskWithSubtasks)
def toggle_pin(task_id: UUID, pinned: bool = True, db=Depends(get_db)):
    """Toggle pin status for a task."""
    task = crud.pin_task(db, task_id, pinned)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/snooze", response_model=TaskWithSubtasks)
def snooze_task(task_id: UUID, until: datetime, db=Depends(get_db)):
    """Snooze a task until a specific time."""
    task = crud.snooze_task(db, task_id, until)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/not-today", response_model=TaskWithSubtasks)
def not_today(task_id: UUID, db=Depends(get_db)):
    """Snooze a task until tomorrow 6am."""
    tomorrow_6am = datetime.combine(
        date.today() + timedelta(days=1),
        datetime.strptime("06:00", "%H:%M").time()
    )
    task = crud.snooze_task(db, task_id, tomorrow_6am)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ============================================
# SUBTASK ENDPOINTS
# ============================================

@router.get("/tasks/{task_id}/subtasks", response_model=List[Subtask])
def list_subtasks(task_id: UUID, db=Depends(get_db)):
    """Get all subtasks for a task."""
    return crud.get_subtasks(db, task_id)


@router.post("/tasks/{task_id}/subtasks", response_model=Subtask, status_code=201)
def create_subtask(task_id: UUID, subtask: SubtaskCreate, db=Depends(get_db)):
    """Create a new subtask."""
    return crud.create_subtask(db, task_id, subtask)


@router.put("/subtasks/{subtask_id}", response_model=Subtask)
def update_subtask(subtask_id: UUID, updates: SubtaskUpdate, db=Depends(get_db)):
    """Update a subtask."""
    subtask = crud.update_subtask(db, subtask_id, updates)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


@router.patch("/subtasks/{subtask_id}/status", response_model=Subtask)
def change_subtask_status(subtask_id: UUID, status: TaskStatus, db=Depends(get_db)):
    """Change subtask status."""
    subtask = crud.update_subtask(db, subtask_id, SubtaskUpdate(status=status))
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


@router.delete("/subtasks/{subtask_id}")
def delete_subtask(subtask_id: UUID, db=Depends(get_db)):
    """Delete a subtask."""
    if not crud.delete_subtask(db, subtask_id):
        raise HTTPException(status_code=404, detail="Subtask not found")
    return {"success": True}


@router.post("/tasks/{task_id}/subtasks/reorder", response_model=List[Subtask])
def reorder_subtasks(task_id: UUID, subtask_ids: List[UUID], db=Depends(get_db)):
    """Reorder subtasks."""
    return crud.reorder_subtasks(db, task_id, subtask_ids)


# ============================================
# VIEW ENDPOINTS
# ============================================

@router.get("/views/today", response_model=TodayViewResponse)
def get_today_view(db=Depends(get_db)):
    """Get the Today view with meetings, ranked tasks, and capacity."""
    today = date.today()
    settings = crud.get_settings(db)

    # Get today's tasks
    tasks = crud.get_today_tasks(db, today)

    # Rank tasks
    ranked_tasks = rank_tasks(tasks, settings)

    # Get today's meetings
    meetings = crud.get_calendar_events(db, today, today)

    # Separate by timebox
    pinned = [t for t in ranked_tasks if t.pinned_today]
    morning = [t for t in ranked_tasks if t.timebox_bucket == TimeboxBucket.MORNING and not t.pinned_today]
    afternoon = [t for t in ranked_tasks if t.timebox_bucket == TimeboxBucket.AFTERNOON and not t.pinned_today]
    evening = [t for t in ranked_tasks if t.timebox_bucket == TimeboxBucket.EVENING and not t.pinned_today]
    unscheduled = [t for t in ranked_tasks if t.timebox_bucket == TimeboxBucket.NONE and not t.pinned_today]

    # Calculate capacity
    capacity_used = sum(t.estimated_minutes or 0 for t in ranked_tasks)

    # Count overdue and pending
    overdue_count = sum(1 for t in ranked_tasks if t.due_date and t.due_date < today)
    pending_count = sum(1 for t in ranked_tasks if t.status == TaskStatus.PENDING)

    return TodayViewResponse(
        date=today,
        meetings=meetings,
        pinned_tasks=pinned,
        morning_tasks=morning,
        afternoon_tasks=afternoon,
        evening_tasks=evening,
        unscheduled_tasks=unscheduled,
        capacity_used_minutes=capacity_used,
        capacity_total_minutes=settings.capacity_minutes_per_day,
        overdue_count=overdue_count,
        pending_count=pending_count,
    )


@router.get("/views/inbox", response_model=InboxViewResponse)
def get_inbox_view(db=Depends(get_db)):
    """Get tasks needing triage."""
    tasks = crud.get_inbox_tasks(db)

    # Categorize
    missing_client = [t for t in tasks if not t.client_id]
    missing_due = [t for t in tasks if not t.due_date]
    # Note: We show tasks missing priority only if they also have another issue
    # since P2 is a valid default

    # Check for duplicates (flagged in raw_source_payload)
    duplicates = [
        t for t in tasks
        if t.raw_source_payload and t.raw_source_payload.get("possible_duplicate")
    ]

    return InboxViewResponse(
        tasks_missing_client=missing_client,
        tasks_missing_due_date=missing_due,
        tasks_missing_priority=[],  # P2 is valid default
        possible_duplicates=duplicates,
        total_count=len(tasks),
    )


@router.get("/views/pending", response_model=PendingViewResponse)
def get_pending_view(db=Depends(get_db)):
    """Get pending/blocked tasks grouped by client."""
    tasks = crud.get_pending_tasks(db)
    today = date.today()

    # Group by client
    clients_dict = {}
    tasks_by_client = {}
    unassigned = []

    for task in tasks:
        if task.client_id:
            client_id_str = str(task.client_id)
            if client_id_str not in tasks_by_client:
                tasks_by_client[client_id_str] = []
                if task.client:
                    clients_dict[client_id_str] = task.client
            tasks_by_client[client_id_str].append(task)
        else:
            unassigned.append(task)

    # Count overdue + pending
    overdue_pending = sum(
        1 for t in tasks
        if t.due_date and t.due_date < today
    )

    # Build client list with counts
    clients = list(clients_dict.values())

    return PendingViewResponse(
        clients=clients,
        tasks_by_client=tasks_by_client,
        unassigned_tasks=unassigned,
        overdue_pending_count=overdue_pending,
        total_count=len(tasks),
    )


@router.get("/views/overdue", response_model=List[TaskWithSubtasks])
def get_overdue_view(db=Depends(get_db)):
    """Get overdue tasks."""
    tasks = crud.get_overdue_tasks(db)
    settings = crud.get_settings(db)
    return rank_tasks(tasks, settings)


@router.get("/views/upcoming", response_model=UpcomingViewResponse)
def get_upcoming_view(days: int = Query(default=7, ge=1, le=90), db=Depends(get_db)):
    """Get upcoming tasks for the next N days."""
    tasks = crud.get_upcoming_tasks(db, days=days)
    settings = crud.get_settings(db)
    ranked = rank_tasks(tasks, settings)

    return UpcomingViewResponse(
        days=days,
        tasks=ranked,
        total_count=len(ranked),
    )


@router.get("/views/completed", response_model=CompletedViewResponse)
def get_completed_view(days: int = Query(default=7, ge=1, le=90), db=Depends(get_db)):
    """Get recently completed tasks."""
    tasks = crud.get_completed_tasks(db, days=days)

    total_minutes = sum(t.estimated_minutes or 0 for t in tasks)

    return CompletedViewResponse(
        days=days,
        tasks=tasks,
        total_count=len(tasks),
        total_estimated_minutes=total_minutes,
    )


# ============================================
# CALENDAR ENDPOINTS
# ============================================

@router.get("/calendar", response_model=List[CalendarEvent])
def list_calendar_events(
    start: date,
    end: date,
    client_id: Optional[UUID] = None,
    db=Depends(get_db),
):
    """Get calendar events in a date range."""
    return crud.get_calendar_events(db, start, end, client_id)


@router.patch("/calendar/{event_id}/client", response_model=CalendarEvent)
def map_event_to_client(
    event_id: UUID,
    client_id: UUID,
    db=Depends(get_db),
):
    """Manually map a calendar event to a client."""
    event = crud.map_event_to_client(db, event_id, client_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ============================================
# SETTINGS ENDPOINTS
# ============================================

@router.get("/settings", response_model=Settings)
def get_settings(db=Depends(get_db)):
    """Get user settings."""
    return crud.get_settings(db)


@router.put("/settings", response_model=Settings)
def update_settings(updates: SettingsUpdate, db=Depends(get_db)):
    """Update user settings."""
    return crud.update_settings(db, updates)


# ============================================
# SEARCH ENDPOINT
# ============================================

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, le=100),
    db=Depends(get_db),
):
    """Full-text search across tasks and clients."""
    tasks = crud.search_tasks(db, q, limit=limit)
    clients = crud.search_clients(db, q, limit=10)

    return SearchResponse(
        query=q,
        tasks=tasks,
        clients=clients,
        total_count=len(tasks) + len(clients),
    )
