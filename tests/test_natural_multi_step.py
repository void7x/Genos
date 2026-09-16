from pathlib import Path

from app.chat.runtime import GenosRuntime


def test_natural_language_multi_step_workflow(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    target = workspace / "sample.py"
    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    tests_dir = workspace / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_sample.py").write_text(
        "from sample import hello\n\n"
        "def test_hello():\n"
        "    assert hello() == 'hello'\n",
        encoding="utf-8",
    )

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    runtime.handle("add goal Improve reliability")

    response = runtime.handle(
        "create a task to add logging to sample.py"
    )

    assert "Multi-step workflow planned." in response
    assert "Add logging to sample.py" in response
    assert "Run the full pytest suite" in response

    runtime.handle("grant safe write")
    runtime.handle("grant execute")

    response = runtime.handle("approve workflow")

    assert "WORKFLOW: COMPLETED" in response

    content = target.read_text(encoding="utf-8")

    assert "import logging" in content
    assert "logger =" in content


def test_natural_multi_step_requires_active_goal(
    tmp_path: Path,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runtime = GenosRuntime(
        workspace,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "create a task to add logging to sample.py"
    )

    assert "Create a goal first" in response
