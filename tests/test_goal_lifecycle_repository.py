from pathlib import Path

from app.goals.lifecycle import GoalLifecycleIntent

import pytest

from app.goals.models import Goal
from app.goals.repository import GoalRepository


def test_update_status_persists_completed_goal(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    original = Goal(
        title="Build a Redis clone",
        description="Implement Redis from scratch",
        priority="high",
    )
    repo.add(original)

    updated = repo.update_status("Build a Redis clone", "completed")

    assert updated is not None
    assert updated.status == "completed"
    assert updated.title == original.title
    assert updated.description == original.description
    assert updated.priority == original.priority
    assert updated.created_at == original.created_at

    loaded = GoalRepository(tmp_path / "goals.json").list()

    assert len(loaded) == 1
    assert loaded[0].status == "completed"


def test_update_status_is_case_insensitive(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))

    updated = repo.update_status("build a redis clone", "paused")

    assert updated is not None
    assert updated.status == "paused"


def test_update_status_returns_none_for_unknown_goal(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))

    assert repo.update_status("Learn Kubernetes", "completed") is None


def test_update_status_rejects_invalid_status(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))

    with pytest.raises(ValueError):
        repo.update_status("Build a Redis clone", "unknown")

def test_apply_complete_intent(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))

    updated = repo.apply_lifecycle_intent(
        GoalLifecycleIntent(
            action="complete",
            goal_title="Build a Redis clone",
        )
    )

    assert updated is not None
    assert updated.status == "completed"


def test_apply_pause_intent(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))

    updated = repo.apply_lifecycle_intent(
        GoalLifecycleIntent(
            action="pause",
            goal_title="Build a Redis clone",
        )
    )

    assert updated is not None
    assert updated.status == "paused"


def test_apply_resume_intent(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")
    repo.add(Goal(title="Build a Redis clone"))
    repo.update_status("Build a Redis clone", "paused")

    updated = repo.apply_lifecycle_intent(
        GoalLifecycleIntent(
            action="resume",
            goal_title="Build a Redis clone",
        )
    )

    assert updated is not None
    assert updated.status == "active"


def test_apply_intent_returns_none_for_unknown_goal(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    result = repo.apply_lifecycle_intent(
        GoalLifecycleIntent(
            action="complete",
            goal_title="Unknown goal",
        )
    )

    assert result is None
