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
