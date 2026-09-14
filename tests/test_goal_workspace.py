from pathlib import Path

import pytest

from app.goals.models import Goal
from app.goals.repository import GoalRepository


def test_goals_are_scoped_to_workspace(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    first = repo.add(
        Goal(title="Build Redis"),
        "workspace-a",
    )
    second = repo.add(
        Goal(title="Build Redis"),
        "workspace-b",
    )

    assert first.workspace_id == "workspace-a"
    assert second.workspace_id == "workspace-b"

    assert repo.list("workspace-a") == [first]
    assert repo.list("workspace-b") == [second]


def test_same_title_allowed_in_different_workspaces(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    repo.add(Goal(title="Run tests"), "workspace-a")
    repo.add(Goal(title="Run tests"), "workspace-b")

    assert len(repo.list("workspace-a")) == 1
    assert len(repo.list("workspace-b")) == 1


def test_duplicate_title_still_deduplicates_inside_workspace(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    first = repo.add(
        Goal(title="Run tests"),
        "workspace-a",
    )
    second = repo.add(
        Goal(title="run tests"),
        "workspace-a",
    )

    stored = repo.list("workspace-a")

    assert len(stored) == 1
    assert stored[0] == first
    assert second.title == "run tests"


def test_workspace_goal_persists(tmp_path: Path):
    path = tmp_path / "goals.json"

    repo = GoalRepository(path)
    goal = repo.add(
        Goal(
            title="Ship project",
            priority="high",
        ),
        "workspace-a",
    )

    loaded = GoalRepository(path).list("workspace-a")

    assert loaded == [goal]


def test_goal_status_update_is_workspace_scoped(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    first = repo.add(
        Goal(title="Fix bug"),
        "workspace-a",
    )
    second = repo.add(
        Goal(title="Fix bug"),
        "workspace-b",
    )

    updated = repo.update_status(
        "Fix bug",
        "completed",
        "workspace-a",
    )

    assert updated is not None
    assert updated.workspace_id == "workspace-a"
    assert updated.status == "completed"

    assert repo.list("workspace-a")[0].status == "completed"
    assert repo.list("workspace-b")[0] == second


def test_empty_workspace_id_is_rejected(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    with pytest.raises(ValueError, match="Workspace ID cannot be empty"):
        repo.list("")

    with pytest.raises(ValueError, match="Workspace ID cannot be empty"):
        repo.add(Goal(title="Test"), "   ")


def test_legacy_unscoped_goals_remain_supported(tmp_path: Path):
    path = tmp_path / "goals.json"
    repo = GoalRepository(path)

    goal = Goal(title="Legacy goal")
    repo.add(goal)

    loaded = GoalRepository(path).list()

    assert loaded == [goal]
    assert loaded[0].workspace_id == ""
