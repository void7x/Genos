import pytest

from app.goals.lifecycle import GoalLifecycleIntent


def test_valid_lifecycle_intent():
    intent = GoalLifecycleIntent(
        action="complete",
        goal_title="Build a Redis clone",
    )

    assert intent.action == "complete"
    assert intent.goal_title == "Build a Redis clone"


def test_action_is_normalized():
    intent = GoalLifecycleIntent(
        action=" PAUSE ",
        goal_title="  Build   a Redis clone  ",
    )

    assert intent.action == "pause"
    assert intent.goal_title == "Build a Redis clone"


def test_invalid_action_rejected():
    with pytest.raises(ValueError):
        GoalLifecycleIntent(
            action="delete",
            goal_title="Build a Redis clone",
        )


def test_empty_goal_title_rejected():
    with pytest.raises(ValueError):
        GoalLifecycleIntent(
            action="complete",
            goal_title="   ",
        )
