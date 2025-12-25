"""
Digest email content rendering.

Generates HTML content for morning and evening digest emails.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from .models import (
    TaskWithSubtasks, CalendarEvent, TaskStatus, TaskPriority,
    DigestRenderResponse,
)
from . import crud
from .ranking import rank_tasks


def render_digest(db, digest_type: str, target_date: date) -> DigestRenderResponse:
    """
    Render digest email content.

    Args:
        db: Supabase client
        digest_type: "morning" or "evening"
        target_date: Date for the digest

    Returns:
        DigestRenderResponse with subject, HTML, and structured sections
    """
    settings = crud.get_settings(db)

    if digest_type == "morning":
        return render_morning_digest(db, target_date, settings)
    else:
        return render_evening_digest(db, target_date, settings)


def render_morning_digest(db, target_date: date, settings) -> DigestRenderResponse:
    """Render morning digest: What's ahead today."""
    # Get today's data
    today_tasks = crud.get_today_tasks(db, target_date)
    ranked_tasks = rank_tasks(today_tasks, settings)
    meetings = crud.get_calendar_events(db, target_date, target_date)
    overdue = crud.get_overdue_tasks(db, target_date)
    pending = crud.get_pending_tasks(db)

    # Build sections
    sections = {
        "date": target_date.isoformat(),
        "meetings_count": len(meetings),
        "tasks_count": len(ranked_tasks),
        "overdue_count": len(overdue),
        "pending_count": len(pending),
        "capacity_used": sum(t.estimated_minutes or 0 for t in ranked_tasks),
        "capacity_total": settings.capacity_minutes_per_day,
    }

    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #a855f7; margin-bottom: 5px; }}
        h2 {{ color: #4a4a6a; border-bottom: 2px solid #a855f7; padding-bottom: 5px; margin-top: 25px; }}
        .subtitle {{ color: #6a6a8a; margin-top: 0; }}
        .stat-bar {{ display: flex; gap: 15px; margin: 15px 0; }}
        .stat {{ background: #f5f5ff; padding: 10px 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #a855f7; }}
        .stat-label {{ font-size: 12px; color: #6a6a8a; }}
        .meeting {{ background: #f0f0ff; padding: 10px; border-radius: 6px; margin: 8px 0; border-left: 3px solid #a855f7; }}
        .meeting-time {{ font-weight: bold; color: #a855f7; }}
        .task {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
        .task:last-child {{ border-bottom: none; }}
        .task-title {{ font-weight: 500; }}
        .task-meta {{ font-size: 13px; color: #6a6a8a; }}
        .priority-P0 {{ color: #dc2626; font-weight: bold; }}
        .priority-P1 {{ color: #ea580c; }}
        .priority-P2 {{ color: #2563eb; }}
        .priority-P3 {{ color: #6b7280; }}
        .overdue {{ color: #dc2626; }}
        .pending {{ color: #f59e0b; }}
        .client-badge {{ background: #a855f7; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
        .empty {{ color: #9ca3af; font-style: italic; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #9ca3af; text-align: center; }}
    </style>
</head>
<body>
    <h1>Good Morning</h1>
    <p class="subtitle">{target_date.strftime('%A, %B %d, %Y')}</p>

    <div class="stat-bar">
        <div class="stat">
            <div class="stat-value">{len(meetings)}</div>
            <div class="stat-label">Meetings</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(ranked_tasks)}</div>
            <div class="stat-label">Tasks</div>
        </div>
        <div class="stat">
            <div class="stat-value" class="overdue">{len(overdue)}</div>
            <div class="stat-label">Overdue</div>
        </div>
        <div class="stat">
            <div class="stat-value" class="pending">{len(pending)}</div>
            <div class="stat-label">Pending</div>
        </div>
    </div>
"""

    # Meetings section
    if meetings:
        html += "<h2>Today's Meetings</h2>"
        for meeting in sorted(meetings, key=lambda m: m.start_time):
            time_str = meeting.start_time.strftime("%I:%M %p")
            client_badge = f'<span class="client-badge">{meeting.client.name}</span>' if meeting.client else ''
            html += f"""
    <div class="meeting">
        <span class="meeting-time">{time_str}</span> - {meeting.title} {client_badge}
    </div>
"""

    # Top tasks section
    html += "<h2>Today's Focus</h2>"
    if ranked_tasks:
        for task in ranked_tasks[:10]:  # Top 10
            priority_class = f"priority-{task.priority.value}"
            client_badge = f'<span class="client-badge">{task.client.name}</span>' if task.client else ''
            due_str = ""
            if task.due_date:
                if task.due_date < target_date:
                    due_str = f'<span class="overdue">Overdue {(target_date - task.due_date).days}d</span>'
                elif task.due_date == target_date:
                    due_str = "Due today"

            html += f"""
    <div class="task">
        <div class="task-title"><span class="{priority_class}">[{task.priority.value}]</span> {task.title} {client_badge}</div>
        <div class="task-meta">{due_str} {f'· {task.estimated_minutes}m' if task.estimated_minutes else ''}</div>
    </div>
"""
    else:
        html += '<p class="empty">No tasks for today</p>'

    # Overdue section
    if overdue:
        html += f"<h2>Overdue ({len(overdue)})</h2>"
        for task in overdue[:5]:
            days = (target_date - task.due_date).days if task.due_date else 0
            client_badge = f'<span class="client-badge">{task.client.name}</span>' if task.client else ''
            html += f"""
    <div class="task">
        <div class="task-title"><span class="overdue">{days}d overdue</span> {task.title} {client_badge}</div>
    </div>
"""

    # Pending section
    if pending:
        html += f"<h2>Blocked ({len(pending)})</h2>"
        for task in pending[:5]:
            client_badge = f'<span class="client-badge">{task.client.name}</span>' if task.client else ''
            waiting = task.waiting_on or task.blocked_reason or "Unknown blocker"
            html += f"""
    <div class="task">
        <div class="task-title"><span class="pending">Waiting:</span> {waiting}</div>
        <div class="task-meta">{task.title} {client_badge}</div>
    </div>
"""

    html += """
    <div class="footer">
        Generated by Client Hub · <a href="#">Open Dashboard</a>
    </div>
</body>
</html>
"""

    subject = f"Morning Digest: {len(meetings)} meetings, {len(ranked_tasks)} tasks for {target_date.strftime('%b %d')}"

    return DigestRenderResponse(
        subject=subject,
        html=html,
        sections=sections,
    )


def render_evening_digest(db, target_date: date, settings) -> DigestRenderResponse:
    """Render evening digest: What happened today and what's tomorrow."""
    # Get today's completed tasks
    completed_today = crud.get_completed_tasks(db, days=1)

    # Get tomorrow's outlook
    tomorrow = target_date + timedelta(days=1)
    tomorrow_tasks = crud.get_today_tasks(db, tomorrow)
    tomorrow_meetings = crud.get_calendar_events(db, tomorrow, tomorrow)

    # Build sections
    sections = {
        "date": target_date.isoformat(),
        "completed_count": len(completed_today),
        "completed_minutes": sum(t.estimated_minutes or 0 for t in completed_today),
        "tomorrow_tasks": len(tomorrow_tasks),
        "tomorrow_meetings": len(tomorrow_meetings),
    }

    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #a855f7; margin-bottom: 5px; }}
        h2 {{ color: #4a4a6a; border-bottom: 2px solid #a855f7; padding-bottom: 5px; margin-top: 25px; }}
        .subtitle {{ color: #6a6a8a; margin-top: 0; }}
        .stat-bar {{ display: flex; gap: 15px; margin: 15px 0; }}
        .stat {{ background: #f5f5ff; padding: 10px 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #a855f7; }}
        .stat-label {{ font-size: 12px; color: #6a6a8a; }}
        .completed {{ color: #16a34a; }}
        .task {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .task:last-child {{ border-bottom: none; }}
        .client-badge {{ background: #a855f7; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
        .empty {{ color: #9ca3af; font-style: italic; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #9ca3af; text-align: center; }}
    </style>
</head>
<body>
    <h1>Evening Wrap-up</h1>
    <p class="subtitle">{target_date.strftime('%A, %B %d, %Y')}</p>

    <div class="stat-bar">
        <div class="stat">
            <div class="stat-value completed">{len(completed_today)}</div>
            <div class="stat-label">Completed</div>
        </div>
        <div class="stat">
            <div class="stat-value">{sections['completed_minutes']}m</div>
            <div class="stat-label">Time Logged</div>
        </div>
    </div>
"""

    # Completed tasks
    if completed_today:
        html += "<h2>Completed Today</h2>"
        for task in completed_today[:10]:
            client_badge = f'<span class="client-badge">{task.client.name}</span>' if task.client else ''
            html += f"""
    <div class="task">
        <span class="completed">✓</span> {task.title} {client_badge}
    </div>
"""
    else:
        html += '<p class="empty">No tasks completed today</p>'

    # Tomorrow preview
    html += f"<h2>Tomorrow's Preview</h2>"
    html += f"<p>{len(tomorrow_meetings)} meetings · {len(tomorrow_tasks)} tasks</p>"

    if tomorrow_meetings:
        for meeting in sorted(tomorrow_meetings, key=lambda m: m.start_time)[:3]:
            time_str = meeting.start_time.strftime("%I:%M %p")
            html += f"<div class='task'><strong>{time_str}</strong> - {meeting.title}</div>"

    html += """
    <div class="footer">
        Generated by Client Hub · <a href="#">Open Dashboard</a>
    </div>
</body>
</html>
"""

    subject = f"Evening Digest: {len(completed_today)} tasks completed, tomorrow: {len(tomorrow_meetings)} meetings"

    return DigestRenderResponse(
        subject=subject,
        html=html,
        sections=sections,
    )
