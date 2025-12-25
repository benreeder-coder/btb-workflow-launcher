"""
Client Hub - Task Management Module

This module provides a comprehensive task management system integrated into
the BTB AI Workflow Launcher. It includes:

- Task and subtask management with statuses, priorities, and timeboxing
- Client management with health tracking
- Calendar event syncing and client matching
- Activity logging for audit trails
- Webhook endpoints for n8n integration
- Ranking algorithms for daily prioritization
- Recurring task generation
- Digest email rendering
"""

# Import ranking functions
from .ranking import rank_tasks, calculate_task_rank, explain_rank

# Import recurring task functions
from .recurring import generate_recurring_instances, parse_rrule_description

# Import digest functions
from .digest import render_digest

from .models import (
    # Enums
    TaskStatus,
    TaskPriority,
    TimeboxBucket,
    SourceType,
    ClientStatus,
    HealthStatus,
    ActorType,
    ActionType,
    EntityType,
    # Client models
    Client,
    ClientCreate,
    ClientUpdate,
    ClientWithCounts,
    # Task models
    Task,
    TaskCreate,
    TaskUpdate,
    TaskWithSubtasks,
    # Subtask models
    Subtask,
    SubtaskCreate,
    SubtaskUpdate,
    # Activity log
    ActivityLog,
    # Calendar
    CalendarEvent,
    CalendarEventCreate,
    # Settings
    Settings,
    SettingsUpdate,
    RankingWeights,
    ClientMatchingRules,
)

__all__ = [
    # Enums
    "TaskStatus",
    "TaskPriority",
    "TimeboxBucket",
    "SourceType",
    "ClientStatus",
    "HealthStatus",
    "ActorType",
    "ActionType",
    "EntityType",
    # Client models
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "ClientWithCounts",
    # Task models
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskWithSubtasks",
    # Subtask models
    "Subtask",
    "SubtaskCreate",
    "SubtaskUpdate",
    # Activity log
    "ActivityLog",
    # Calendar
    "CalendarEvent",
    "CalendarEventCreate",
    # Settings
    "Settings",
    "SettingsUpdate",
    "RankingWeights",
    "ClientMatchingRules",
]
