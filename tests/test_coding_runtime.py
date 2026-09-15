from pathlib import Path

from app.chat import GenosRuntime


def test_runtime_plans_logging_edit(tmp_path: Path):
    target = tmp_path / "sample.py"

    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    response = runtime.handle("add logging to sample.py")

    assert "Plan:" in response
    assert "sample.py" in response
    assert "SAFE_WRITE" in response
    assert runtime.workflow.pending is not None
    assert runtime.workflow.pending.plan.action == "edit"


def test_runtime_executes_approved_logging_edit(tmp_path: Path):
    target = tmp_path / "sample.py"

    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("add logging to sample.py")

    denied = runtime.handle("approve")
    assert "Permission denied: SAFE_WRITE" in denied

    runtime.handle("give me permission to edit files")

    result = runtime.handle("approve")

    assert "ACT: SUCCESS" in result
    assert "VERIFY: PASSED" in result
    assert "REMEMBER: Saved" in result

    content = target.read_text(encoding="utf-8")

    assert "import logging" in content
    assert "logger = logging.getLogger(__name__)" in content
    assert 'logger.debug("Entering hello")' in content


def test_runtime_coding_change_records_action_history(tmp_path: Path):
    target = tmp_path / "sample.py"

    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("add logging to sample.py")
    runtime.handle("grant safe write")

    result = runtime.handle("approve")

    assert "ACT: SUCCESS" in result
    assert "VERIFY: PASSED" in result

    entries = runtime.history.list(runtime.workspace.id)

    assert len(entries) == 1
    assert entries[0].action == "edit"
    assert entries[0].target == "sample.py"
    assert entries[0].status == "success"
    assert entries[0].verification == "passed"


def test_runtime_direct_write_records_action_history(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("grant safe write")

    response = runtime.handle(
        "write file hello.txt :: hello"
    )

    assert "hello.txt" in response

    entries = runtime.history.list(runtime.workspace.id)

    assert len(entries) == 1
    assert entries[0].action == "write"
    assert entries[0].target == "hello.txt"
    assert entries[0].status == "success"


def test_runtime_direct_execute_records_action_history(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("grant execute")

    response = runtime.handle(
        "execute python --version"
    )

    assert response is not None

    entries = runtime.history.list(runtime.workspace.id)

    assert len(entries) == 1
    assert entries[0].action == "execute"
    assert entries[0].status == "success"


