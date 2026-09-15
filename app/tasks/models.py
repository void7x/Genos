from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


TASK_STATUSES = {
    "planned",
    "in_progress",
    "completed",
    "failed",
    "cancelled",
}


@dataclass(frozen=True)
class Task:
    title: str
    goal_title: str
    workspace_id: str
    status: str = "planned"
    id: str = field(default="")
    created_at: str = field(default="")
    updated_at: str = field(default="")

    def __post_init__(self) -> None:
        title = " ".join(self.title.strip().split())
        goal_title = " ".join(self.goal_title.strip().split())
        workspace_id = self.workspace_id.strip()
        status = self.status.strip().lower()

        if not title:
            raise ValueError("Task title cannot be empty.")

        if not goal_title:
            raise ValueError("Goal title cannot be empty.")

        if not workspace_id:
            raise ValueError("Workspace ID cannot be empty.")

        if status not in TASK_STATUSES:
            raise ValueError(
                f"Unsupported task status: {status}"
            )

        now = datetime.now(timezone.utc).isoformat()

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "goal_title", goal_title)
        object.__setattr__(self, "workspace_id", workspace_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "id",
            self.id or uuid.uuid4().hex[:16],
        )
        object.__setattr__(
            self,
            "created_at",
            self.created_at or now,
        )
        object.__setattr__(
            self,
            "updated_at",
            self.updated_at or now,
        )


class TaskRepository:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workspace_id: str) -> Path:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        safe_name = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return self.root / safe_name / "tasks.json"

    def list(
        self,
        workspace_id: str,
    ) -> list[Task]:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized)

        if not path.exists():
            return []

        try:
            raw = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(raw, list):
            return []

        tasks: list[Task] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            try:
                tasks.append(
                    Task(
                        title=item.get("title", ""),
                        goal_title=item.get("goal_title", ""),
                        workspace_id=item.get(
                            "workspace_id",
                            "",
                        ),
                        status=item.get(
                            "status",
                            "planned",
                        ),
                        id=item.get("id", ""),
                        created_at=item.get(
                            "created_at",
                            "",
                        ),
                        updated_at=item.get(
                            "updated_at",
                            "",
                        ),
                    )
                )
            except ValueError:
                continue

        return [
            task
            for task in tasks
            if task.workspace_id == normalized
        ]

    def save(
        self,
        workspace_id: str,
        tasks: list[Task],
    ) -> None:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                [asdict(task) for task in tasks],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def add(
        self,
        task: Task,
    ) -> Task:
        tasks = self.list(task.workspace_id)

        for existing in tasks:
            if (
                existing.title.casefold()
                == task.title.casefold()
                and existing.goal_title.casefold()
                == task.goal_title.casefold()
            ):
                return existing

        tasks.append(task)
        self.save(task.workspace_id, tasks)

        return task

    def update_status(
        self,
        workspace_id: str,
        task_id: str,
        status: str,
    ) -> Task | None:
        normalized_workspace = str(workspace_id).strip()
        normalized_id = str(task_id).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        if not normalized_id:
            return None

        tasks = self.list(normalized_workspace)

        for index, existing in enumerate(tasks):
            if existing.id != normalized_id:
                continue

            updated = Task(
                title=existing.title,
                goal_title=existing.goal_title,
                workspace_id=existing.workspace_id,
                status=status,
                id=existing.id,
                created_at=existing.created_at,
                updated_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )

            tasks[index] = updated
            self.save(normalized_workspace, tasks)

            return updated

        return None
