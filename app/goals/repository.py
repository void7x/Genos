from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from app.goals.lifecycle import GoalLifecycleIntent
from app.goals.models import Goal


class GoalRepository:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _path(self, workspace_id: str | None = None) -> Path:
        if workspace_id is None:
            return self.path

        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        safe_name = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        scoped_root = self.path.parent / f"{self.path.stem}_workspaces"
        return scoped_root / safe_name / self.path.name

    def list(self, workspace_id: str | None = None) -> list[Goal]:
        path = self._path(workspace_id)

        if not path.exists():
            return []

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw, list):
            return []

        goals: list[Goal] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            try:
                stored_workspace = str(item.get("workspace_id", "")).strip()

                goals.append(
                    Goal(
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        status=item.get("status", "active"),
                        priority=item.get("priority", "medium"),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        workspace_id=stored_workspace,
                    )
                )
            except ValueError:
                continue

        if workspace_id is None:
            return goals

        normalized = str(workspace_id).strip()

        return [
            goal
            for goal in goals
            if goal.workspace_id == normalized
        ]

    def save(
        self,
        goals: list[Goal],
        workspace_id: str | None = None,
    ) -> None:
        path = self._path(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = [asdict(goal) for goal in goals]

        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(
        self,
        goal: Goal,
        workspace_id: str | None = None,
    ) -> Goal:
        normalized_workspace = (
            goal.workspace_id
            if workspace_id is None
            else str(workspace_id).strip()
        )

        if workspace_id is not None and not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        scoped_goal = (
            goal
            if goal.workspace_id == normalized_workspace
            else Goal(
                title=goal.title,
                description=goal.description,
                status=goal.status,
                priority=goal.priority,
                created_at=goal.created_at,
                updated_at=goal.updated_at,
                workspace_id=normalized_workspace,
            )
        )

        goals = self.list(workspace_id)

        if any(
            existing.title.casefold() == scoped_goal.title.casefold()
            for existing in goals
        ):
            return scoped_goal

        goals.append(scoped_goal)
        self.save(goals, workspace_id)

        return scoped_goal

    def update_status(
        self,
        title: str,
        status: str,
        workspace_id: str | None = None,
    ) -> Goal | None:
        normalized_title = " ".join(title.strip().split())

        if not normalized_title:
            return None

        normalized_status = status.strip().lower()
        goals = self.list(workspace_id)

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
                workspace_id=existing.workspace_id,
            )

            goals[index] = updated
            self.save(goals, workspace_id)
            return updated

        return None

    def apply_lifecycle_intent(
        self,
        intent: GoalLifecycleIntent,
        workspace_id: str | None = None,
    ) -> Goal | None:
        status_by_action = {
            "complete": "completed",
            "pause": "paused",
            "resume": "active",
            "cancel": "cancelled",
        }

        status = status_by_action[intent.action]

        return self.update_status(
            intent.goal_title,
            status,
            workspace_id,
        )
