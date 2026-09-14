from pathlib import Path

import pytest

from app.tools import ProjectTools


def tools_for(tmp_path: Path) -> ProjectTools:
    return ProjectTools(tmp_path)


def test_list_files(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    (tmp_path / "app" / "main.py").write_text("print('hi')", encoding="utf-8")

    result = tools_for(tmp_path).list_files()

    assert result.success is True
    assert "app/" in result.output
    assert "README.md" in result.output


def test_read_file(tmp_path: Path):
    file_path = tmp_path / "README.md"
    file_path.write_text("Genos project", encoding="utf-8")

    result = tools_for(tmp_path).read_file("README.md")

    assert result.success is True
    assert result.output == "Genos project"


def test_search_files(tmp_path: Path):
    (tmp_path / "one.txt").write_text("Python FastAPI", encoding="utf-8")
    (tmp_path / "two.txt").write_text("React frontend", encoding="utf-8")

    result = tools_for(tmp_path).search_files("FastAPI")

    assert result.success is True
    assert result.output == "one.txt"


def test_git_tools_work_inside_git_workspace(tmp_path: Path):
    subprocess = __import__("subprocess")
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "genos@test.local"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Genos Test"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    file_path = tmp_path / "README.md"
    file_path.write_text("initial", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    tools = tools_for(tmp_path)

    status = tools.git_status()
    log = tools.git_log(5)
    diff = tools.git_diff()

    assert status.success is True
    assert status.output == ""
    assert log.success is True
    assert "initial" in log.output
    assert diff.success is True


def test_tool_rejects_workspace_escape(tmp_path: Path):
    tools = tools_for(tmp_path)

    with pytest.raises(ValueError, match="escapes"):
        tools.read_file("../outside.txt")


def test_tool_rejects_absolute_path(tmp_path: Path):
    tools = tools_for(tmp_path)

    with pytest.raises(ValueError, match="relative"):
        tools.read_file(str(tmp_path / "file.txt"))


def test_empty_search_is_rejected(tmp_path: Path):
    result = tools_for(tmp_path).search_files("   ")

    assert result.success is False
    assert "empty" in result.error


def test_missing_file_returns_failure(tmp_path: Path):
    result = tools_for(tmp_path).read_file("missing.txt")

    assert result.success is False
    assert "Not a file" in result.error


def test_list_missing_directory_returns_failure(tmp_path: Path):
    result = tools_for(tmp_path).list_files("missing")

    assert result.success is False
    assert "Not a directory" in result.error


def test_git_log_rejects_invalid_limit(tmp_path: Path):
    result = tools_for(tmp_path).git_log(0)

    assert result.success is False
    assert "positive" in result.error
