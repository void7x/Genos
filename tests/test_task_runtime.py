from app.chat.runtime import GenosRuntime


def test_runtime_adds_and_lists_task(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    runtime._add_goal(
        "Improve authentication reliability"
    )

    response = runtime.handle(
        "add task Add logging to auth.py"
    )

    assert "Task created:" in response
    assert "Improve authentication reliability" in response

    tasks = runtime.handle("show tasks")

    assert "Add logging to auth.py" in tasks
    assert "planned" in tasks


def test_runtime_shows_current_task(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    runtime._add_goal("Improve reliability")
    runtime.handle("add task Add logs")

    response = runtime.handle("show current task")

    assert "Current task:" in response
    assert "Add logs" in response
    assert "Improve reliability" in response
