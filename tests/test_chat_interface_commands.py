from pathlib import Path

from app.chat.intent import IntentRouter


def test_inspect_project_intent():
    intent = IntentRouter().route("inspect this project")
    assert intent.name == "project_info"


def test_git_diff_intent():
    intent = IntentRouter().route("show git diff")
    assert intent.name == "git_diff"


def test_recent_git_history_intent():
    intent = IntentRouter().route("show recent git history")
    assert intent.name == "git_log"


def test_add_goal_intent():
    intent = IntentRouter().route(
        "add goal Improve reliability"
    )

    assert intent.name == "goal"
    assert intent.argument == "Improve reliability"


def test_goal_lifecycle_intent():
    intent = IntentRouter().route(
        "pause goal Improve reliability"
    )

    assert intent.name == "goal_lifecycle"
    assert intent.argument == (
        "pause :: Improve reliability"
    )


def test_last_file_intent():
    intent = IntentRouter().route(
        "what file did you just find"
    )

    assert intent.name == "last_file"


def test_action_history_intent():
    intent = IntentRouter().route(
        "show action history"
    )

    assert intent.name == "action_history"
