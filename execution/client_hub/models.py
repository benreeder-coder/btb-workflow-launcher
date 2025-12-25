"""
Pydantic models for Client Hub.

These models define the data structures for:
- Clients (companies)
- Tasks and subtasks
- Calendar events
- Activity logs
- Settings
"""
from datetime import date, time, datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================
# ENUMS
# ============================================

class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class TaskPriority(str, Enum):
    P0 = "P0"  # Critical/Urgent
    P1 = "P1"  # High
    P2 = "P2"  # Medium (default)
    P3 = "P3"  # Low


class TimeboxBucket(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    NONE = "NONE"


class SourceType(str, Enum):
    MANUAL = "MANUAL"
    N8N = "N8N"
    FIREFLIES = "FIREFLIES"
    CALENDAR = "CALENDAR"


class ClientStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CHURNED = "churned"
    PROSPECT = "prospect"


class HealthStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class ActorType(str, Enum):
    MANUAL = "MANUAL"
    N8N = "N8N"
    SYSTEM = "SYSTEM"


class ActionType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    RESTORED = "RESTORED"
    STATUS_CHANGED = "STATUS_CHANGED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    DUE_DATE_CHANGED = "DUE_DATE_CHANGED"
    INGESTED = "INGESTED"
    DEDUPE_MERGE = "DEDUPE_MERGE"
    RECURRENCE_GENERATED = "RECURRENCE_GENERATED"
    SUBTASK_ADDED = "SUBTASK_ADDED"
    SUBTASK_COMPLETED = "SUBTASK_COMPLETED"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"


class EntityType(str, Enum):
    TASK = "TASK"
    SUBTASK = "SUBTASK"
    CLIENT = "CLIENT"
    SETTINGS = "SETTINGS"
    CALENDAR_EVENT = "CALENDAR_EVENT"


# ============================================
# CLIENT MODELS
# ============================================

class ClientBase(BaseModel):
    """Base client fields."""
    name: str = Field(..., min_length=1, max_length=255)
    status: ClientStatus = ClientStatus.ACTIVE
    color_hex: str = Field(default="#a855f7", pattern=r"^#[0-9A-Fa-f]{6}$")
    default_priority_weight: int = Field(default=0, ge=0, le=20)
    health_status: Optional[HealthStatus] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClientCreate(ClientBase):
    """Fields for creating a new client."""
    pass


class ClientUpdate(BaseModel):
    """Fields for updating a client (all optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ClientStatus] = None
    color_hex: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    default_priority_weight: Optional[int] = Field(None, ge=0, le=20)
    health_status: Optional[HealthStatus] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Client(ClientBase):
    """Full client model with database fields."""
    id: UUID
    last_touched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientWithCounts(Client):
    """Client with task counts for list views."""
    total_tasks: int = 0
    open_tasks: int = 0
    overdue_tasks: int = 0
    pending_tasks: int = 0


# ============================================
# SUBTASK MODELS
# ============================================

class SubtaskBase(BaseModel):
    """Base subtask fields."""
    title: str = Field(..., min_length=1, max_length=500)
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None


class SubtaskCreate(SubtaskBase):
    """Fields for creating a new subtask."""
    order_rank: Optional[int] = None


class SubtaskUpdate(BaseModel):
    """Fields for updating a subtask (all optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    order_rank: Optional[int] = None
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None


class Subtask(SubtaskBase):
    """Full subtask model with database fields."""
    id: UUID
    task_id: UUID
    order_rank: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# TASK MODELS
# ============================================

class TaskBase(BaseModel):
    """Base task fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.P2
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    start_date: Optional[date] = None
    timebox_bucket: TimeboxBucket = TimeboxBucket.NONE
    estimated_minutes: Optional[int] = Field(None, ge=0)
    pinned_today: bool = False
    tags: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None
    client_id: Optional[UUID] = None

    @field_validator('due_time', mode='before')
    @classmethod
    def parse_time(cls, v):
        """Parse time from string format."""
        if v is None or v == '':
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            # Handle "HH:MM" or "HH:MM:SS" formats
            try:
                if ':' in v:
                    parts = v.split(':')
                    if len(parts) == 2:
                        return time(int(parts[0]), int(parts[1]))
                    elif len(parts) == 3:
                        return time(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass
        return v


class TaskCreate(TaskBase):
    """Fields for creating a new task."""
    # Recurring fields
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # RRULE format
    recurrence_timezone: str = "America/New_York"
    recurrence_anchor_date: Optional[date] = None
    recurrence_end_date: Optional[date] = None
    recurrence_skip_weekends: bool = False

    # Source tracking
    source_type: SourceType = SourceType.MANUAL
    source_id: Optional[str] = None
    transcript_id: Optional[str] = None
    meeting_id: Optional[str] = None
    source_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    raw_source_payload: Optional[Dict[str, Any]] = None

    # Subtasks to create with the task
    subtasks: List[SubtaskCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Fields for updating a task (all optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    start_date: Optional[date] = None
    snooze_until: Optional[datetime] = None
    timebox_bucket: Optional[TimeboxBucket] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    pinned_today: Optional[bool] = None
    tags: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None
    client_id: Optional[UUID] = None

    # Recurring updates
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    recurrence_skip_weekends: Optional[bool] = None


class Task(TaskBase):
    """Full task model with database fields."""
    id: UUID

    # Scheduling
    snooze_until: Optional[datetime] = None

    # Recurring
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_timezone: str = "America/New_York"
    recurrence_anchor_date: Optional[date] = None
    next_occurrence_at: Optional[datetime] = None
    recurrence_end_date: Optional[date] = None
    recurrence_skip_weekends: bool = False
    parent_recurring_task_id: Optional[UUID] = None

    # Source tracking
    source_type: SourceType = SourceType.MANUAL
    source_id: Optional[str] = None
    transcript_id: Optional[str] = None
    meeting_id: Optional[str] = None
    source_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    raw_source_payload: Optional[Dict[str, Any]] = None
    schema_version: int = 1

    # Edit tracking
    last_edited_source: SourceType = SourceType.MANUAL
    last_edited_at: Optional[datetime] = None
    manually_edited: bool = False
    manual_fields: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    # Computed fields (set by ranking algorithm)
    rank_score: Optional[float] = None

    class Config:
        from_attributes = True


class TaskWithSubtasks(Task):
    """Task with its subtasks included."""
    subtasks: List[Subtask] = Field(default_factory=list)
    client: Optional[Client] = None

    # Computed field for completion percentage
    @property
    def subtask_progress(self) -> float:
        if not self.subtasks:
            return 1.0
        completed = sum(1 for s in self.subtasks if s.status == TaskStatus.COMPLETED)
        return completed / len(self.subtasks)


# ============================================
# ACTIVITY LOG MODELS
# ============================================

class ActivityLog(BaseModel):
    """Activity log entry for audit trail."""
    id: UUID
    entity_type: EntityType
    entity_id: UUID
    action_type: ActionType
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changes: Optional[Dict[str, Any]] = None
    actor: ActorType = ActorType.MANUAL
    source_info: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogCreate(BaseModel):
    """Fields for creating an activity log entry."""
    entity_type: EntityType
    entity_id: UUID
    action_type: ActionType
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changes: Optional[Dict[str, Any]] = None
    actor: ActorType = ActorType.MANUAL
    source_info: Optional[Dict[str, Any]] = None


# ============================================
# CALENDAR EVENT MODELS
# ============================================

class Attendee(BaseModel):
    """Calendar event attendee."""
    email: str
    name: Optional[str] = None
    response_status: Optional[str] = None


class CalendarEventBase(BaseModel):
    """Base calendar event fields."""
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    timezone: str = "America/New_York"
    attendees: List[Attendee] = Field(default_factory=list)
    organizer_email: Optional[str] = None


class CalendarEventCreate(CalendarEventBase):
    """Fields for creating/upserting a calendar event."""
    gcal_event_id: str
    calendar_id: Optional[str] = None
    client_id: Optional[UUID] = None
    match_confidence: Optional[int] = Field(None, ge=0, le=100)
    match_method: Optional[str] = None
    etag: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class CalendarEvent(CalendarEventBase):
    """Full calendar event model."""
    id: UUID
    gcal_event_id: str
    calendar_id: Optional[str] = None
    client_id: Optional[UUID] = None
    client: Optional[Client] = None
    match_confidence: Optional[int] = None
    match_method: Optional[str] = None
    etag: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None
    synced_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# SETTINGS MODELS
# ============================================

class RankingWeights(BaseModel):
    """Configurable weights for task ranking algorithm."""
    overdue: int = 100
    due_today: int = 60
    priority_p0: int = 50
    priority_p1: int = 30
    priority_p2: int = 15
    priority_p3: int = 0
    in_progress: int = 10
    pending: int = -10
    client_weight_multiplier: float = 1.0


class DomainRule(BaseModel):
    """Maps email domain to client."""
    domain: str
    client_id: UUID


class KeywordRule(BaseModel):
    """Maps keyword to client."""
    keyword: str
    client_id: UUID


class OverrideRule(BaseModel):
    """Manual override for specific calendar event."""
    gcal_event_id: str
    client_id: UUID


class ClientMatchingRules(BaseModel):
    """Rules for matching calendar events to clients."""
    domains: List[DomainRule] = Field(default_factory=list)
    keywords: List[KeywordRule] = Field(default_factory=list)
    overrides: List[OverrideRule] = Field(default_factory=list)


class Settings(BaseModel):
    """User settings (singleton row)."""
    id: UUID = Field(default="00000000-0000-0000-0000-000000000001")
    timezone: str = "America/New_York"
    work_start_time: time = time(9, 0)
    work_end_time: time = time(17, 0)
    capacity_minutes_per_day: int = 360
    morning_end: time = time(12, 0)
    afternoon_end: time = time(17, 0)
    morning_digest_time: Optional[time] = time(6, 0)
    evening_digest_time: Optional[time] = time(21, 0)
    digest_enabled: bool = True
    ranking_weights: RankingWeights = Field(default_factory=RankingWeights)
    client_matching_rules: ClientMatchingRules = Field(default_factory=ClientMatchingRules)
    default_task_duration_minutes: int = 30
    auto_archive_completed_days: int = 7
    show_completed_in_today: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    """Fields for updating settings (all optional)."""
    timezone: Optional[str] = None
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    capacity_minutes_per_day: Optional[int] = Field(None, ge=60, le=720)
    morning_end: Optional[time] = None
    afternoon_end: Optional[time] = None
    morning_digest_time: Optional[time] = None
    evening_digest_time: Optional[time] = None
    digest_enabled: Optional[bool] = None
    ranking_weights: Optional[RankingWeights] = None
    client_matching_rules: Optional[ClientMatchingRules] = None
    default_task_duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    auto_archive_completed_days: Optional[int] = Field(None, ge=1, le=365)
    show_completed_in_today: Optional[bool] = None


# ============================================
# VIEW RESPONSE MODELS
# ============================================

class TodayViewResponse(BaseModel):
    """Response for the Today view endpoint."""
    date: date
    meetings: List[CalendarEvent] = Field(default_factory=list)
    pinned_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    morning_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    afternoon_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    evening_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    unscheduled_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    capacity_used_minutes: int = 0
    capacity_total_minutes: int = 360
    overdue_count: int = 0
    pending_count: int = 0


class InboxViewResponse(BaseModel):
    """Response for the Inbox view endpoint."""
    tasks_missing_client: List[TaskWithSubtasks] = Field(default_factory=list)
    tasks_missing_due_date: List[TaskWithSubtasks] = Field(default_factory=list)
    tasks_missing_priority: List[TaskWithSubtasks] = Field(default_factory=list)
    possible_duplicates: List[TaskWithSubtasks] = Field(default_factory=list)
    total_count: int = 0


class PendingViewResponse(BaseModel):
    """Response for the Pending view endpoint."""
    clients: List[ClientWithCounts] = Field(default_factory=list)
    tasks_by_client: Dict[str, List[TaskWithSubtasks]] = Field(default_factory=dict)
    unassigned_tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    overdue_pending_count: int = 0
    total_count: int = 0


class UpcomingViewResponse(BaseModel):
    """Response for the Upcoming view endpoint."""
    days: int = 7
    tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    total_count: int = 0


class CompletedViewResponse(BaseModel):
    """Response for the Completed view endpoint."""
    days: int = 7
    tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    total_count: int = 0
    total_estimated_minutes: int = 0


class SearchResponse(BaseModel):
    """Response for search endpoint."""
    query: str
    tasks: List[TaskWithSubtasks] = Field(default_factory=list)
    clients: List[Client] = Field(default_factory=list)
    total_count: int = 0


# ============================================
# WEBHOOK PAYLOAD MODELS
# ============================================

class WebhookSource(BaseModel):
    """Source information for webhook payloads."""
    type: str = "N8N"
    workflow_id: Optional[str] = None
    run_id: Optional[str] = None


class WebhookTaskClient(BaseModel):
    """Client info in webhook task payload."""
    name: str
    domain: Optional[str] = None


class WebhookSubtask(BaseModel):
    """Subtask in webhook task payload."""
    title: str
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None


class WebhookTask(BaseModel):
    """Task in webhook upsert payload."""
    idempotency_key: str
    source_type: SourceType = SourceType.FIREFLIES
    source_id: str
    transcript_id: Optional[str] = None
    meeting_id: Optional[str] = None
    source_url: Optional[str] = None
    client: Optional[WebhookTaskClient] = None
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.P2
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    start_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    timebox_bucket: Optional[TimeboxBucket] = None
    waiting_on: Optional[str] = None
    blocked_reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_anchor_date: Optional[date] = None
    recurrence_end_date: Optional[date] = None
    recurrence_skip_weekends: bool = False
    subtasks: List[WebhookSubtask] = Field(default_factory=list)
    raw_source_payload: Optional[Dict[str, Any]] = None


class WebhookTasksUpsertPayload(BaseModel):
    """Payload for POST /api/webhooks/tasks/upsert."""
    schema_version: int = 1
    ingested_at: datetime
    source: WebhookSource
    tasks: List[WebhookTask]


class WebhookCalendarEvent(BaseModel):
    """Calendar event in webhook payload."""
    gcal_event_id: str
    calendar_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    attendees: List[Attendee] = Field(default_factory=list)
    organizer_email: Optional[str] = None
    etag: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class WebhookCalendarUpsertPayload(BaseModel):
    """Payload for POST /api/webhooks/calendar/upsert."""
    schema_version: int = 1
    synced_at: datetime
    source: WebhookSource
    events: List[WebhookCalendarEvent]


class DigestRenderRequest(BaseModel):
    """Request for POST /api/digest/render."""
    type: str = Field(..., pattern="^(morning|evening)$")
    date: date


class DigestRenderResponse(BaseModel):
    """Response for POST /api/digest/render."""
    subject: str
    html: str
    sections: Dict[str, Any]
