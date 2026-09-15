from app.chat.runtime import GenosRuntime


def test_add_task_uses_newest_active_goal(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    runtime.handle(
        "add goal Older goal"
    )

    runtime.handle(
        "add goal Newer goal"
    )

    response = runtime.handle(
        "add task Test newest goal selection"
    )

    assert "Goal: Newer goal" in response

    tasks = runtime.tasks.list(
        runtime.workspace.id
    )

    assert len(tasks) == 1
    assert tasks[0].goal_title == "Newer goal"
