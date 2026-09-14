from pathlib import Path

from app.chat import GenosRuntime


def runtime_for(tmp_path: Path) -> GenosRuntime:
    return GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )


def test_chat_uses_orchestrator_for_find_and_explain(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle(
        "find PermissionManager and explain it"
    )

    assert "I found" in response
    assert "app\\permissions\\manager.py" in response
    assert "PermissionLevel" in response


def test_chat_uses_orchestrator_for_project_analysis(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle(
        "analyze this project"
    )

    assert "Project diagnosis:" in response
    assert "Name: Genos" in response
    assert "Type: Python" in response
