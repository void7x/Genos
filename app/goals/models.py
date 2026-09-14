"""Structured long-term goals for Genos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


GOAL_STATUSES = {
    "active",
    "paused",
    "completed",
    "cancelled",
}

GOAL_PRIORITIES = {
    "low",
    "medium",
    "high",
}


@dataclass(frozen=True)
class Goal:
    title: str
    description: str = ""
    status: str = "active"
    priority: str = "medium"
    created_at: str = field(default="", compare=False)
    updated_at: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        title = " ".join(self.title.strip().split())
        description = " ".join(self.description.strip().split())
        status = self.status.strip().lower()
        priority = self.priority.strip().lower()

        if not title:
            raise ValueError("Goal title cannot be empty.")

        if status not in GOAL_STATUSES:
            raise ValueError(f"Unsupported goal status: {status}")

        if priority not in GOAL_PRIORITIES:
            raise ValueError(f"Unsupported goal priority: {priority}")

        now = datetime.now(timezone.utc).isoformat()

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "priority", priority)
        object.__setattr__(self, "created_at", self.created_at or now)
        object.__setattr__(self, "updated_at", self.updated_at or now)
