from __future__ import annotations

from app.tasks.models import Task, TaskRepository


class TaskManager:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def list(self, workspace_id: str) -> list[Task]:
        return self.repository.list(workspace_id)

    def add(
        self,
        workspace_id: str,
        title: str,
        goal_title: str,
    ) -> Task:
        return self.repository.add(
            Task(
                title=title,
                goal_title=goal_title,
                workspace_id=workspace_id,
            )
        )

    def get(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Task | None:
        normalized = str(task_id).strip()

        if not normalized:
            return None

        return next(
            (
                task
                for task in self.list(workspace_id)
                if task.id == normalized
            ),
            None,
        )

    def current(self, workspace_id: str) -> Task | None:
        tasks = self.list(workspace_id)

        for status in ("in_progress", "planned"):
            match = next(
                (
                    task
                    for task in tasks
                    if task.status == status
                ),
                None,
            )

            if match is not None:
                return match

        return None

    def start(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Task | None:
        return self.repository.update_status(
            workspace_id,
            task_id,
            "in_progress",
        )

    def complete(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Task | None:
        return self.repository.update_status(
            workspace_id,
            task_id,
            "completed",
        )

    def fail(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Task | None:
        return self.repository.update_status(
            workspace_id,
            task_id,
            "failed",
        )
