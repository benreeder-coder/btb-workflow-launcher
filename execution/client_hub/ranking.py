"""
Task Ranking Algorithm for Client Hub.

Calculates priority scores for tasks based on configurable weights.
Higher score = higher priority (appears first in lists).
"""
from datetime import date, datetime, timezone
from typing import List, Optional

from .models import Task, TaskWithSubtasks, TaskStatus, TaskPriority, Settings, RankingWeights


def calculate_task_rank(
    task: TaskWithSubtasks,
    settings: Settings,
    today: Optional[date] = None,
) -> float:
    """
    Calculate rank score for a single task.

    Factors:
    1. Pinned status (+1000 to always appear first)
    2. Priority (P0=50, P1=30, P2=15, P3=0 by default)
    3. Due date urgency (overdue gets +100, due today +60)
    4. Status modifiers (IN_PROGRESS +10, PENDING -10)
    5. Client priority weight (0-20, multiplied by client_weight_multiplier)

    Returns:
        Float score where higher = more urgent
    """
    if today is None:
        today = date.today()

    weights = settings.ranking_weights
    score = 0.0

    # 1. Pinned tasks always first
    if task.pinned_today:
        score += 1000

    # 2. Priority score
    priority_scores = {
        TaskPriority.P0: weights.priority_p0,
        TaskPriority.P1: weights.priority_p1,
        TaskPriority.P2: weights.priority_p2,
        TaskPriority.P3: weights.priority_p3,
    }
    score += priority_scores.get(task.priority, weights.priority_p2)

    # 3. Due date urgency
    if task.due_date:
        days_until = (task.due_date - today).days

        if days_until < 0:
            # Overdue: base overdue score + extra per day overdue (capped)
            overdue_days = min(abs(days_until), 30)  # Cap at 30 days
            score += weights.overdue + (overdue_days * 2)
        elif days_until == 0:
            # Due today
            score += weights.due_today
        elif days_until <= 3:
            # Due within 3 days - graduated urgency
            score += weights.due_today * (0.8 - (days_until * 0.2))
        elif days_until <= 7:
            # Due within a week
            score += weights.due_today * 0.3

    # 4. Status modifiers
    if task.status == TaskStatus.IN_PROGRESS:
        score += weights.in_progress
    elif task.status == TaskStatus.PENDING:
        score += weights.pending  # Usually negative

    # 5. Client priority weight
    if task.client and task.client.default_priority_weight:
        score += task.client.default_priority_weight * weights.client_weight_multiplier

    # 6. Age bonus (slight FIFO preference for similar tasks)
    if task.created_at:
        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        # Make created_at timezone-aware if it isn't
        created = task.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (now - created).days
        score += min(age_days * 0.1, 5)  # Max +5 points for age

    return round(score, 2)


def rank_tasks(
    tasks: List[TaskWithSubtasks],
    settings: Settings,
    today: Optional[date] = None,
) -> List[TaskWithSubtasks]:
    """
    Sort tasks by rank score (descending).

    Args:
        tasks: List of tasks to rank
        settings: User settings containing ranking weights
        today: Reference date for calculations (defaults to today)

    Returns:
        List of tasks sorted by rank score (highest first)
    """
    if today is None:
        today = date.today()

    # Calculate rank scores
    for task in tasks:
        task.rank_score = calculate_task_rank(task, settings, today)

    # Sort by rank score descending
    return sorted(tasks, key=lambda t: t.rank_score or 0, reverse=True)


def explain_rank(
    task: TaskWithSubtasks,
    settings: Settings,
    today: Optional[date] = None,
) -> dict:
    """
    Explain why a task has its rank score.

    Useful for debugging and showing "Why ranked" tooltips.

    Returns:
        Dictionary with score breakdown
    """
    if today is None:
        today = date.today()

    weights = settings.ranking_weights
    breakdown = {
        "total": 0.0,
        "components": [],
    }

    # Pinned
    if task.pinned_today:
        breakdown["components"].append({
            "factor": "Pinned",
            "score": 1000,
            "reason": "Task is pinned for today"
        })
        breakdown["total"] += 1000

    # Priority
    priority_scores = {
        TaskPriority.P0: weights.priority_p0,
        TaskPriority.P1: weights.priority_p1,
        TaskPriority.P2: weights.priority_p2,
        TaskPriority.P3: weights.priority_p3,
    }
    priority_score = priority_scores.get(task.priority, 0)
    breakdown["components"].append({
        "factor": "Priority",
        "score": priority_score,
        "reason": f"Priority {task.priority.value}"
    })
    breakdown["total"] += priority_score

    # Due date
    if task.due_date:
        days_until = (task.due_date - today).days
        due_score = 0

        if days_until < 0:
            overdue_days = min(abs(days_until), 30)
            due_score = weights.overdue + (overdue_days * 2)
            reason = f"Overdue by {abs(days_until)} day(s)"
        elif days_until == 0:
            due_score = weights.due_today
            reason = "Due today"
        elif days_until <= 3:
            due_score = weights.due_today * (0.8 - (days_until * 0.2))
            reason = f"Due in {days_until} day(s)"
        elif days_until <= 7:
            due_score = weights.due_today * 0.3
            reason = f"Due in {days_until} days"
        else:
            reason = f"Due in {days_until} days (no urgency)"

        if due_score != 0:
            breakdown["components"].append({
                "factor": "Due Date",
                "score": round(due_score, 2),
                "reason": reason
            })
            breakdown["total"] += due_score

    # Status
    status_score = 0
    if task.status == TaskStatus.IN_PROGRESS:
        status_score = weights.in_progress
        reason = "In progress"
    elif task.status == TaskStatus.PENDING:
        status_score = weights.pending
        reason = "Pending/blocked"

    if status_score != 0:
        breakdown["components"].append({
            "factor": "Status",
            "score": status_score,
            "reason": reason
        })
        breakdown["total"] += status_score

    # Client priority
    if task.client and task.client.default_priority_weight:
        client_score = task.client.default_priority_weight * weights.client_weight_multiplier
        breakdown["components"].append({
            "factor": "Client Priority",
            "score": round(client_score, 2),
            "reason": f"{task.client.name} has priority weight {task.client.default_priority_weight}"
        })
        breakdown["total"] += client_score

    breakdown["total"] = round(breakdown["total"], 2)
    return breakdown
