"""Persistent storage for structured goals."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from app.goals.lifecycle import GoalLifecycleIntent
from app.goals.models import Goal


class GoalRepository:
    """Store goals as JSON while keeping storage details out of the rest of Mereum."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def list(self) -> list[Goal]:
        if not self.path.exists():
            return []

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw, list):
            return []

        goals: list[Goal] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            try:
                goals.append(
                    Goal(
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        status=item.get("status", "active"),
                        priority=item.get("priority", "medium"),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                    )
                )
            except ValueError:
                continue

        return goals

    def save(self, goals: list[Goal]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = [asdict(goal) for goal in goals]

        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, goal: Goal) -> Goal:
        goals = self.list()

        if any(
            existing.title.casefold() == goal.title.casefold()
            for existing in goals
        ):
            return goal

        goals.append(goal)
        self.save(goals)
        return goal

    def update_status(self, title: str, status: str) -> Goal | None:
        """Update an existing goal's status and persist the change."""
        normalized_title = " ".join(title.strip().split())

        if not normalized_title:
            return None

        normalized_status = status.strip().lower()

        goals = self.list()

        for index, existing in enumerate(goals):
            if existing.title.casefold() != normalized_title.casefold():
                continue

            updated = Goal(
                title=existing.title,
                description=existing.description,
                status=normalized_status,
                priority=existing.priority,
                created_at=existing.created_at,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

            goals[index] = updated
            self.save(goals)
            return updated

        return None

    def apply_lifecycle_intent(
        self,
        intent: GoalLifecycleIntent,
    ) -> Goal | None:
        """Apply a lifecycle action to an existing goal."""
        status_by_action = {
            "complete": "completed",
            "pause": "paused",
            "resume": "active",
            "cancel": "cancelled",
        }

        status = status_by_action[intent.action]

        return self.update_status(intent.goal_title, status)
