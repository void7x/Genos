import pytest

from app.goals.models import Goal


def test_goal_defaults():
    goal = Goal(title="Finish Redis clone")

    assert goal.title == "Finish Redis clone"
    assert goal.description == ""
    assert goal.status == "active"
    assert goal.priority == "medium"
    assert goal.created_at
    assert goal.updated_at


def test_goal_normalizes_text():
    goal = Goal(
        title="  Finish   Redis   clone  ",
        description="  Build the server   from scratch  ",
        status=" ACTIVE ",
        priority=" HIGH ",
    )

    assert goal.title == "Finish Redis clone"
    assert goal.description == "Build the server from scratch"
    assert goal.status == "active"
    assert goal.priority == "high"


@pytest.mark.parametrize(
    "status",
    ["active", "paused", "completed", "cancelled"],
)
def test_supported_goal_statuses(status):
    goal = Goal(
        title="Test goal",
        status=status,
    )

    assert goal.status == status


@pytest.mark.parametrize(
    "priority",
    ["low", "medium", "high"],
)
def test_supported_goal_priorities(priority):
    goal = Goal(
        title="Test goal",
        priority=priority,
    )

    assert goal.priority == priority


def test_empty_goal_title_is_rejected():
    with pytest.raises(ValueError):
        Goal(title="   ")


@pytest.mark.parametrize(
    "status",
    ["", "unknown", "done"],
)
def test_invalid_goal_status_is_rejected(status):
    with pytest.raises(ValueError):
        Goal(
            title="Test goal",
            status=status,
        )


@pytest.mark.parametrize(
    "priority",
    ["", "urgent", "critical"],
)
def test_invalid_goal_priority_is_rejected(priority):
    with pytest.raises(ValueError):
        Goal(
            title="Test goal",
            priority=priority,
        )


def test_explicit_timestamps_are_preserved():
    goal = Goal(
        title="Build Mereum",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-02-01T00:00:00+00:00",
    )

    assert goal.created_at == "2026-01-01T00:00:00+00:00"
    assert goal.updated_at == "2026-02-01T00:00:00+00:00"


def test_goal_is_immutable():
    goal = Goal(title="Build Mereum")

    with pytest.raises(Exception):
        goal.status = "completed"
