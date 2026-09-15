from app.tasks import TaskManager, TaskRepository


def test_current_prefers_in_progress(tmp_path):
    manager = TaskManager(
        TaskRepository(tmp_path / "tasks")
    )

    planned = manager.add(
        "workspace-a",
        "Planned",
        "Goal",
    )
    active = manager.add(
        "workspace-a",
        "Active",
        "Goal",
    )

    manager.start("workspace-a", active.id)

    current = manager.current("workspace-a")

    assert current is not None
    assert current.id == active.id
    assert current.id != planned.id


def test_current_returns_planned_when_no_active_task(
    tmp_path,
):
    manager = TaskManager(
        TaskRepository(tmp_path / "tasks")
    )

    task = manager.add(
        "workspace-a",
        "Task",
        "Goal",
    )

    current = manager.current("workspace-a")

    assert current == task


def test_task_lifecycle_helpers(tmp_path):
    manager = TaskManager(
        TaskRepository(tmp_path / "tasks")
    )

    task = manager.add(
        "workspace-a",
        "Task",
        "Goal",
    )

    started = manager.start(
        "workspace-a",
        task.id,
    )
    completed = manager.complete(
        "workspace-a",
        task.id,
    )

    assert started is not None
    assert started.status == "in_progress"
    assert completed is not None
    assert completed.status == "completed"
