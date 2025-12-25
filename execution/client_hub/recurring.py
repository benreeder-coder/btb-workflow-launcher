"""
Recurring Task Generation.

Handles RRULE parsing and generating task instances from recurring templates.
Uses on-demand generation when loading Today/Upcoming views.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from dateutil.rrule import rrulestr
from dateutil.tz import gettz

from .models import (
    TaskWithSubtasks, TaskCreate, SubtaskCreate,
    TaskStatus, SourceType, ActorType, ActionType, EntityType,
)
from . import crud


def generate_recurring_instances(
    db,
    up_to_date: date,
    timezone: str = "America/New_York",
) -> List[TaskWithSubtasks]:
    """
    Generate recurring task instances up to a given date.

    This should be called when loading Today or Upcoming views.
    It finds recurring tasks where next_occurrence_at <= up_to_date
    and generates new instances.

    Returns list of newly created task instances.
    """
    tz = gettz(timezone)
    now = datetime.now(tz)
    created_instances = []

    # Find recurring tasks that need instances generated
    result = db.table("tasks").select("*").eq(
        "is_recurring", True
    ).is_("archived_at", "null").lte(
        "next_occurrence_at", up_to_date.isoformat()
    ).execute()

    for row in result.data:
        try:
            instances = generate_instances_for_task(
                db, row, up_to_date, timezone
            )
            created_instances.extend(instances)
        except Exception as e:
            print(f"Error generating instances for task {row['id']}: {e}")

    return created_instances


def generate_instances_for_task(
    db,
    recurring_task: dict,
    up_to_date: date,
    timezone: str = "America/New_York",
) -> List[TaskWithSubtasks]:
    """
    Generate instances for a single recurring task.
    """
    tz = gettz(timezone)
    created = []

    rrule_str = recurring_task.get("recurrence_rule")
    if not rrule_str:
        return []

    # Parse the RRULE
    try:
        # Get the anchor date (first occurrence)
        anchor = recurring_task.get("recurrence_anchor_date")
        if anchor:
            dtstart = datetime.combine(
                date.fromisoformat(anchor) if isinstance(anchor, str) else anchor,
                datetime.min.time()
            ).replace(tzinfo=tz)
        else:
            dtstart = datetime.now(tz)

        rule = rrulestr(rrule_str, dtstart=dtstart)
    except Exception as e:
        print(f"Invalid RRULE for task {recurring_task['id']}: {e}")
        return []

    # Get next occurrence(s) up to the target date
    next_occurrence_str = recurring_task.get("next_occurrence_at")
    if next_occurrence_str:
        current = datetime.fromisoformat(
            next_occurrence_str.replace('Z', '+00:00')
        ).date()
    else:
        current = date.today()

    end_date = recurring_task.get("recurrence_end_date")
    if end_date:
        end_date = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date

    skip_weekends = recurring_task.get("recurrence_skip_weekends", False)

    # Generate instances for each occurrence up to up_to_date
    while current <= up_to_date:
        # Check end date
        if end_date and current > end_date:
            break

        # Skip weekends if configured
        if skip_weekends and current.weekday() >= 5:
            # Move to next Monday
            days_until_monday = 7 - current.weekday()
            current = current + timedelta(days=days_until_monday)
            continue

        # Check if instance already exists for this date
        existing = db.table("tasks").select("id").eq(
            "parent_recurring_task_id", recurring_task["id"]
        ).eq("due_date", current.isoformat()).execute()

        if not existing.data:
            # Create instance
            instance = create_recurring_instance(
                db, recurring_task, current
            )
            if instance:
                created.append(instance)

        # Get next occurrence
        try:
            next_dt = rule.after(
                datetime.combine(current, datetime.min.time()).replace(tzinfo=tz)
            )
            if next_dt:
                current = next_dt.date()
            else:
                break
        except StopIteration:
            break

    # Update next_occurrence_at on the recurring task
    try:
        next_dt = rule.after(
            datetime.combine(up_to_date, datetime.min.time()).replace(tzinfo=tz)
        )
        if next_dt:
            db.table("tasks").update({
                "next_occurrence_at": next_dt.isoformat()
            }).eq("id", recurring_task["id"]).execute()
    except Exception:
        pass

    return created


def create_recurring_instance(
    db,
    recurring_task: dict,
    instance_date: date,
) -> Optional[TaskWithSubtasks]:
    """
    Create a single instance of a recurring task.
    """
    # Get subtasks from parent
    subtasks_result = db.table("subtasks").select("*").eq(
        "task_id", recurring_task["id"]
    ).execute()

    subtasks = [
        SubtaskCreate(
            title=s["title"],
            status=TaskStatus.NOT_STARTED,
            priority=s.get("priority"),
        )
        for s in subtasks_result.data
    ]

    # Create the instance
    instance = TaskCreate(
        title=recurring_task["title"],
        description=recurring_task.get("description"),
        status=TaskStatus.NOT_STARTED,
        priority=recurring_task.get("priority", "P2"),
        due_date=instance_date,
        due_time=recurring_task.get("due_time"),
        timebox_bucket=recurring_task.get("timebox_bucket", "NONE"),
        estimated_minutes=recurring_task.get("estimated_minutes"),
        tags=recurring_task.get("tags", []),
        labels=recurring_task.get("labels", []),
        client_id=UUID(recurring_task["client_id"]) if recurring_task.get("client_id") else None,
        source_type=SourceType.MANUAL,
        is_recurring=False,  # Instance is not recurring
        raw_source_payload={
            "parent_recurring_task_id": recurring_task["id"],
            "recurrence_instance_date": instance_date.isoformat(),
        },
        subtasks=subtasks,
    )

    created = crud.create_task(db, instance, actor=ActorType.SYSTEM)

    # Link to parent
    db.table("tasks").update({
        "parent_recurring_task_id": recurring_task["id"]
    }).eq("id", str(created.id)).execute()

    # Log activity
    crud.log_activity(
        db,
        EntityType.TASK,
        created.id,
        ActionType.RECURRENCE_GENERATED,
        actor=ActorType.SYSTEM,
        source_info={
            "parent_task_id": recurring_task["id"],
            "instance_date": instance_date.isoformat(),
        }
    )

    return created


def parse_rrule_description(rrule_str: str) -> str:
    """
    Convert RRULE string to human-readable description.
    """
    try:
        # Parse components
        parts = dict(
            part.split('=') for part in rrule_str.split(';')
            if '=' in part
        )

        freq = parts.get('FREQ', 'DAILY')
        interval = int(parts.get('INTERVAL', 1))
        byday = parts.get('BYDAY', '')

        freq_map = {
            'DAILY': 'day' if interval == 1 else f'{interval} days',
            'WEEKLY': 'week' if interval == 1 else f'{interval} weeks',
            'MONTHLY': 'month' if interval == 1 else f'{interval} months',
            'YEARLY': 'year' if interval == 1 else f'{interval} years',
        }

        base = f"Every {freq_map.get(freq, freq.lower())}"

        if byday:
            day_map = {
                'MO': 'Monday', 'TU': 'Tuesday', 'WE': 'Wednesday',
                'TH': 'Thursday', 'FR': 'Friday', 'SA': 'Saturday', 'SU': 'Sunday'
            }
            days = [day_map.get(d, d) for d in byday.split(',')]
            base += f" on {', '.join(days)}"

        return base

    except Exception:
        return rrule_str  # Return original if parsing fails
