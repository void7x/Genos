from pathlib import Path

from app.chat import GenosRuntime


def runtime_for(tmp_path: Path) -> GenosRuntime:
    return GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )


def test_context_followup_reuses_previous_result(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    first = runtime.handle("git status")
    followup = runtime.handle("what did you find")

    assert first
    assert "Based on the previous step:" in followup
    assert first in followup


def test_context_reads_the_file_it_found(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    found = runtime.handle("find ProjectTools")
    opened = runtime.handle("read the one you found")

    assert "project_tools.py" in found
    assert "ProjectTools" in opened


def test_context_read_that_file_reuses_recent_file(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    runtime.handle("find ProjectTools")
    response = runtime.handle("read that file")

    assert "ProjectTools" in response


def test_context_is_workspace_scoped(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    first.mkdir()
    second.mkdir()

    runtime = GenosRuntime(
        first,
        data_root=tmp_path / "data",
    )

    target = first / "first.txt"
    target.write_text("first workspace", encoding="utf-8")

    runtime.handle("read first.txt")

    runtime.workspace_manager.attach(second)
    runtime.handle("switch to second")

    response = runtime.handle("what did you find")

    assert "There is no previous result" in response
    assert "first workspace" not in response
