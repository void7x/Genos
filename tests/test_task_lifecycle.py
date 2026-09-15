from pathlib import Path

import pytest

from app.tasks import (
    Task,
    TaskRepository,
)


def task_for(tmp_path: Path) -> TaskRepository:
    return TaskRepository(tmp_path / "tasks")


def test_task_defaults_to_planned(tmp_path: Path):
    task = Task(
        title="Add authentication logging",
        goal_title="Improve authentication reliability",
        workspace_id="workspace-a",
    )

    assert task.status == "planned"
    assert task.id
    assert task.created_at
    assert task.updated_at


def test_task_normalizes_fields(tmp_path: Path):
    task = Task(
        title="  Add   logging  ",
        goal_title="  Improve   auth  ",
        workspace_id=" workspace-a ",
        status=" IN_PROGRESS ",
    )

    assert task.title == "Add logging"
    assert task.goal_title == "Improve auth"
    assert task.workspace_id == "workspace-a"
    assert task.status == "in_progress"


@pytest.mark.parametrize(
    "status",
    [
        "planned",
        "in_progress",
        "completed",
        "failed",
        "cancelled",
    ],
)
def test_supported_task_statuses(status, tmp_path: Path):
    task = Task(
        title="Task",
        goal_title="Goal",
        workspace_id="workspace-a",
        status=status,
    )

    assert task.status == status


def test_invalid_status_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        Task(
            title="Task",
            goal_title="Goal",
            workspace_id="workspace-a",
            status="done",
        )


def test_task_persists_and_is_workspace_scoped(tmp_path: Path):
    repository = task_for(tmp_path)

    first = Task(
        title="Task A",
        goal_title="Goal A",
        workspace_id="workspace-a",
    )
    second = Task(
        title="Task B",
        goal_title="Goal B",
        workspace_id="workspace-b",
    )

    repository.add(first)
    repository.add(second)

    assert repository.list("workspace-a") == [first]
    assert repository.list("workspace-b") == [second]


def test_duplicate_task_is_not_added_twice(tmp_path: Path):
    repository = task_for(tmp_path)

    first = Task(
        title="Task A",
        goal_title="Goal A",
        workspace_id="workspace-a",
    )

    second = Task(
        title="Task A",
        goal_title="Goal A",
        workspace_id="workspace-a",
    )

    saved_first = repository.add(first)
    saved_second = repository.add(second)

    assert saved_second == saved_first
    assert len(repository.list("workspace-a")) == 1


def test_task_status_can_progress_to_completed(tmp_path: Path):
    repository = task_for(tmp_path)

    task = repository.add(
        Task(
            title="Add authentication logging",
            goal_title="Improve authentication reliability",
            workspace_id="workspace-a",
        )
    )

    started = repository.update_status(
        "workspace-a",
        task.id,
        "in_progress",
    )
    completed = repository.update_status(
        "workspace-a",
        task.id,
        "completed",
    )

    assert started is not None
    assert started.status == "in_progress"
    assert completed is not None
    assert completed.status == "completed"
    assert completed.id == task.id


def test_missing_task_status_update_returns_none(tmp_path: Path):
    repository = task_for(tmp_path)

    assert repository.update_status(
        "workspace-a",
        "missing",
        "completed",
    ) is None


def test_empty_task_title_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        Task(
            title=" ",
            goal_title="Goal",
            workspace_id="workspace-a",
        )


def test_empty_goal_title_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        Task(
            title="Task",
            goal_title=" ",
            workspace_id="workspace-a",
        )
