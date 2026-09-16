from pathlib import Path

from app.chat import GenosRuntime


def runtime_for(tmp_path: Path) -> GenosRuntime:
    return GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )


def test_help(tmp_path: Path):
    response = runtime_for(tmp_path).handle("help")

    assert "files" in response
    assert "Git status and history" in response


def test_project_info(tmp_path: Path):
    response = runtime_for(tmp_path).handle("what is this project")

    assert "Name: Genos" in response
    assert "Type: Python" in response
    assert "Python" in response


def test_list_files(tmp_path: Path):
    response = runtime_for(tmp_path).handle("list files")

    assert "app/" in response
    assert "tests/" in response


def test_read_readme(tmp_path: Path):
    response = runtime_for(tmp_path).handle("read readme")

    assert "# Genos" in response


def test_find_files(tmp_path: Path):
    response = runtime_for(tmp_path).handle("find ProjectTools")

    assert "project_tools.py" in response


def test_git_status(tmp_path: Path):
    response = runtime_for(tmp_path).handle("git status")

    assert response.strip()


def test_git_log(tmp_path: Path):
    response = runtime_for(tmp_path).handle("git log")

    assert response.strip()


def test_memory_is_workspace_scoped(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle("remember Genos uses workspace-scoped memory")

    assert "Remembered:" in response

    search = runtime.handle("memory workspace-scoped")

    assert "workspace-scoped memory" in search


def test_goals_are_workspace_scoped(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle("goal Build the Genos chatbot")

    assert "Build the Genos chatbot" in response

    goals = runtime.handle("goals")

    assert "Build the Genos chatbot" in goals
