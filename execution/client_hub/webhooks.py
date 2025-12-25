"""
Webhook endpoints for n8n integration.

These endpoints allow n8n to:
- Upsert tasks from Fireflies transcripts
- Sync calendar events from Google Calendar
- Request digest content for morning/evening emails
"""
import os
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Header, Depends

from ..supabase_client import get_supabase, SupabaseClientError
from . import crud
from .models import (
    TaskStatus, TaskPriority, TimeboxBucket, SourceType, ActorType, ActionType, EntityType,
    TaskCreate, SubtaskCreate,
    CalendarEventCreate, Attendee,
    WebhookTasksUpsertPayload, WebhookCalendarUpsertPayload,
    DigestRenderRequest, DigestRenderResponse,
    Settings,
)
from .digest import render_digest

# Create router
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

# Webhook secret from environment
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def verify_webhook_secret(x_webhook_secret: str = Header(...)):
    """Verify webhook secret header."""
    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Webhook secret not configured. Set WEBHOOK_SECRET environment variable."
        )
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return True


def get_db():
    """Dependency to get Supabase client."""
    try:
        return get_supabase()
    except SupabaseClientError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ============================================
# TASK UPSERT WEBHOOK
# ============================================

@router.post("/tasks/upsert")
def upsert_tasks(
    payload: WebhookTasksUpsertPayload,
    _=Depends(verify_webhook_secret),
    db=Depends(get_db),
):
    """
    Idempotent task ingestion from n8n/Fireflies.

    Behavior:
    - Upsert by idempotency_key (primary) or (source_type, source_id) (fallback)
    - Respects manual edit protection
    - Creates activity log entries
    - Handles client matching
    - Detects potential duplicates
    """
    results = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "task_ids": [],
    }

    for task_data in payload.tasks:
        try:
            # Look for existing task by idempotency_key
            existing = None
            if task_data.idempotency_key:
                existing_result = db.table("tasks").select("*").eq(
                    "idempotency_key", task_data.idempotency_key
                ).execute()
                if existing_result.data:
                    existing = existing_result.data[0]

            # Fallback: look by source_type + source_id
            if not existing and task_data.source_id:
                existing_result = db.table("tasks").select("*").eq(
                    "source_type", task_data.source_type.value
                ).eq("source_id", task_data.source_id).execute()
                if existing_result.data:
                    existing = existing_result.data[0]

            if existing:
                # Update existing task
                task_id = UUID(existing["id"])

                # Check manual edit protection
                if existing.get("manually_edited"):
                    protected_fields = existing.get("manual_fields", [])
                    # Only update non-protected fields
                    update_data = {}

                    field_mapping = {
                        "title": task_data.title,
                        "description": task_data.description,
                        "status": task_data.status.value if task_data.status else None,
                        "priority": task_data.priority.value if task_data.priority else None,
                        "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
                        "due_time": str(task_data.due_time) if task_data.due_time else None,
                        "timebox_bucket": task_data.timebox_bucket.value if task_data.timebox_bucket else None,
                        "estimated_minutes": task_data.estimated_minutes,
                        "waiting_on": task_data.waiting_on,
                        "blocked_reason": task_data.blocked_reason,
                    }

                    for field, value in field_mapping.items():
                        if field not in protected_fields and value is not None:
                            update_data[field] = value

                    # Always allowed: append tags/labels (set union)
                    if task_data.tags:
                        existing_tags = existing.get("tags", [])
                        update_data["tags"] = list(set(existing_tags + task_data.tags))
                    if task_data.labels:
                        existing_labels = existing.get("labels", [])
                        update_data["labels"] = list(set(existing_labels + task_data.labels))

                else:
                    # Full update allowed
                    update_data = {
                        "title": task_data.title,
                        "description": task_data.description,
                        "status": task_data.status.value,
                        "priority": task_data.priority.value,
                        "due_date": task_data.due_date.isoformat() if task_data.due_date else None,
                        "due_time": str(task_data.due_time) if task_data.due_time else None,
                        "start_date": task_data.start_date.isoformat() if task_data.start_date else None,
                        "timebox_bucket": task_data.timebox_bucket.value if task_data.timebox_bucket else "NONE",
                        "estimated_minutes": task_data.estimated_minutes,
                        "waiting_on": task_data.waiting_on,
                        "blocked_reason": task_data.blocked_reason,
                        "tags": task_data.tags,
                        "labels": task_data.labels,
                        "raw_source_payload": task_data.raw_source_payload,
                    }

                # Update tracking fields
                update_data["last_edited_source"] = "N8N"
                update_data["last_edited_at"] = datetime.utcnow().isoformat()

                if update_data:
                    db.table("tasks").update(update_data).eq("id", str(task_id)).execute()

                    # Log activity
                    crud.log_activity(
                        db,
                        EntityType.TASK,
                        task_id,
                        ActionType.INGESTED,
                        actor=ActorType.N8N,
                        changes=update_data,
                        source_info={
                            "workflow_id": payload.source.workflow_id,
                            "run_id": payload.source.run_id,
                        }
                    )

                results["updated"] += 1
                results["task_ids"].append(str(task_id))

            else:
                # Create new task
                # Handle client matching
                client_id = None
                if task_data.client:
                    client_id = match_or_create_client(
                        db,
                        task_data.client.name,
                        task_data.client.domain,
                    )

                # Check for potential duplicates
                possible_duplicate = check_duplicate(
                    db,
                    client_id,
                    task_data.title,
                    task_data.due_date,
                )

                raw_payload = task_data.raw_source_payload or {}
                if possible_duplicate:
                    raw_payload["possible_duplicate"] = True
                    raw_payload["duplicate_of"] = str(possible_duplicate)

                # Create task
                new_task = TaskCreate(
                    title=task_data.title,
                    description=task_data.description,
                    status=task_data.status,
                    priority=task_data.priority,
                    due_date=task_data.due_date,
                    due_time=task_data.due_time,
                    start_date=task_data.start_date,
                    timebox_bucket=task_data.timebox_bucket or TimeboxBucket.NONE,
                    estimated_minutes=task_data.estimated_minutes,
                    waiting_on=task_data.waiting_on,
                    blocked_reason=task_data.blocked_reason,
                    tags=task_data.tags,
                    labels=task_data.labels,
                    client_id=client_id,
                    source_type=task_data.source_type,
                    source_id=task_data.source_id,
                    transcript_id=task_data.transcript_id,
                    meeting_id=task_data.meeting_id,
                    source_url=task_data.source_url,
                    idempotency_key=task_data.idempotency_key,
                    raw_source_payload=raw_payload,
                    is_recurring=task_data.is_recurring,
                    recurrence_rule=task_data.recurrence_rule,
                    recurrence_anchor_date=task_data.recurrence_anchor_date,
                    recurrence_end_date=task_data.recurrence_end_date,
                    recurrence_skip_weekends=task_data.recurrence_skip_weekends,
                    subtasks=[
                        SubtaskCreate(
                            title=s.title,
                            status=s.status,
                            priority=s.priority,
                            due_date=s.due_date,
                            waiting_on=s.waiting_on,
                            blocked_reason=s.blocked_reason,
                        )
                        for s in task_data.subtasks
                    ],
                )

                created = crud.create_task(db, new_task, actor=ActorType.N8N)
                results["created"] += 1
                results["task_ids"].append(str(created.id))

        except Exception as e:
            results["errors"].append({
                "idempotency_key": task_data.idempotency_key,
                "error": str(e),
            })

    return {
        "success": len(results["errors"]) == 0,
        "results": results,
    }


def match_or_create_client(
    db,
    name: str,
    domain: Optional[str],
) -> Optional[UUID]:
    """Match existing client or create new one."""
    # Try to find by name (case-insensitive)
    result = db.table("clients").select("id").ilike("name", name).execute()
    if result.data:
        return UUID(result.data[0]["id"])

    # Try to find by domain if provided
    if domain:
        # Get settings for domain matching rules
        settings = crud.get_settings(db)
        for rule in settings.client_matching_rules.domains:
            if rule.domain.lower() == domain.lower():
                return rule.client_id

    # Create new client
    from .models import ClientCreate
    new_client = crud.create_client(
        db,
        ClientCreate(name=name),
        actor=ActorType.N8N,
    )
    return new_client.id


def check_duplicate(
    db,
    client_id: Optional[UUID],
    title: str,
    due_date: Optional[date],
) -> Optional[UUID]:
    """
    Check if a similar task already exists.
    Returns the ID of the potential duplicate, or None.
    """
    if not client_id:
        return None

    query = db.table("tasks").select("id, title, due_date").eq(
        "client_id", str(client_id)
    ).ilike("title", title).is_("archived_at", "null")

    result = query.execute()

    for existing in result.data:
        # Check if due dates are within 1 day
        if due_date and existing.get("due_date"):
            existing_date = date.fromisoformat(existing["due_date"])
            if abs((due_date - existing_date).days) <= 1:
                return UUID(existing["id"])
        elif not due_date and not existing.get("due_date"):
            # Both have no due date
            return UUID(existing["id"])

    return None


# ============================================
# CALENDAR UPSERT WEBHOOK
# ============================================

@router.post("/calendar/upsert")
def upsert_calendar_events(
    payload: WebhookCalendarUpsertPayload,
    _=Depends(verify_webhook_secret),
    db=Depends(get_db),
):
    """
    Sync calendar events from n8n (Google Calendar).

    Behavior:
    - Upsert by gcal_event_id
    - Apply client matching rules (domain, keyword, override)
    - Store raw event data
    """
    results = {
        "upserted": 0,
        "errors": [],
    }

    settings = crud.get_settings(db)

    for event_data in payload.events:
        try:
            # Match client
            client_id, confidence, method = match_event_to_client(
                settings,
                event_data.title,
                event_data.attendees,
                event_data.gcal_event_id,
            )

            # Create event
            event = CalendarEventCreate(
                gcal_event_id=event_data.gcal_event_id,
                calendar_id=event_data.calendar_id,
                title=event_data.title,
                description=event_data.description,
                location=event_data.location,
                meeting_link=event_data.meeting_link,
                start_time=event_data.start_time,
                end_time=event_data.end_time,
                all_day=event_data.all_day,
                attendees=event_data.attendees,
                organizer_email=event_data.organizer_email,
                client_id=client_id,
                match_confidence=confidence,
                match_method=method,
                etag=event_data.etag,
                raw=event_data.raw,
            )

            crud.upsert_calendar_event(db, event)
            results["upserted"] += 1

        except Exception as e:
            results["errors"].append({
                "gcal_event_id": event_data.gcal_event_id,
                "error": str(e),
            })

    return {
        "success": len(results["errors"]) == 0,
        "results": results,
    }


def match_event_to_client(
    settings: Settings,
    title: str,
    attendees: list,
    gcal_event_id: str,
) -> tuple[Optional[UUID], Optional[int], Optional[str]]:
    """
    Match a calendar event to a client using configured rules.

    Priority:
    1. Manual overrides by gcal_event_id
    2. Attendee email domain matching
    3. Keyword matching in title

    Returns: (client_id, confidence, method)
    """
    rules = settings.client_matching_rules

    # 1. Check overrides
    for override in rules.overrides:
        if override.gcal_event_id == gcal_event_id:
            return override.client_id, 100, "override"

    # 2. Check attendee domains
    for attendee in attendees:
        email = attendee.email if hasattr(attendee, 'email') else attendee.get('email', '')
        if '@' in email:
            domain = email.split('@')[1].lower()
            for rule in rules.domains:
                if rule.domain.lower() == domain:
                    return rule.client_id, 90, "domain"

    # 3. Check keywords in title
    title_lower = title.lower()
    for rule in rules.keywords:
        if rule.keyword.lower() in title_lower:
            return rule.client_id, 70, "keyword"

    return None, None, None


# ============================================
# DIGEST RENDER ENDPOINT
# ============================================

@router.post("/digest/render", response_model=DigestRenderResponse)
def render_digest_endpoint(
    request: DigestRenderRequest,
    _=Depends(verify_webhook_secret),
    db=Depends(get_db),
):
    """
    Render digest email content for n8n to send.

    Returns HTML content for morning or evening digest.
    """
    return render_digest(db, request.type, request.date)
