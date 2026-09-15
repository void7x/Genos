from pathlib import Path

from app.chat.runtime import GenosRuntime


def test_runtime_goal_lifecycle_commands(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    runtime.handle(
        "add goal Improve reliability"
    )

    paused = runtime.handle(
        "pause goal Improve reliability"
    )

    resumed = runtime.handle(
        "resume goal Improve reliability"
    )

    completed = runtime.handle(
        "complete goal Improve reliability"
    )

    assert "Status: paused" in paused
    assert "Status: active" in resumed
    assert "Status: completed" in completed


def test_runtime_show_git_diff(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "show git diff"
    )

    assert isinstance(response, str)


def test_runtime_action_history_command(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "show action history"
    )

    assert "action history" in response.casefold()
