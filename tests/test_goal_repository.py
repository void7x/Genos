from pathlib import Path

from app.goals.models import Goal
from app.goals.repository import GoalRepository


def test_repository_starts_empty(tmp_path: Path):
    repo = GoalRepository(tmp_path / "goals.json")

    assert repo.list() == []


def test_repository_persists_goal(tmp_path: Path):
    path = tmp_path / "goals.json"

    repo = GoalRepository(path)
    goal = Goal(
        title="Build a Redis clone",
        description="Implement Redis from scratch",
        priority="high",
    )

    repo.add(goal)

    loaded = GoalRepository(path).list()

    assert loaded == [goal]


def test_repository_deduplicates_title(tmp_path: Path):
    path = tmp_path / "goals.json"
    repo = GoalRepository(path)

    first = Goal(title="Build a Redis clone")
    second = Goal(title="build a redis clone")

    repo.add(first)
    repo.add(second)

    loaded = repo.list()

    assert len(loaded) == 1
    assert loaded[0].title == "Build a Redis clone"


def test_repository_ignores_invalid_records(tmp_path: Path):
    path = tmp_path / "goals.json"
    path.write_text(
        '[{"title": "Valid goal"}, {"title": ""}, {"broken": true}]',
        encoding="utf-8",
    )

    loaded = GoalRepository(path).list()

    assert len(loaded) == 1
    assert loaded[0].title == "Valid goal"


def test_repository_handles_non_list_json(tmp_path: Path):
    path = tmp_path / "goals.json"
    path.write_text('{"goal": "bad"}', encoding="utf-8")

    assert GoalRepository(path).list() == []
