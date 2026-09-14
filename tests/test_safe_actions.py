from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools


def actions_for(tmp_path: Path) -> ProjectActionTools:
    return ProjectActionTools(
        tmp_path,
        PermissionManager(),
    )


def test_write_requires_safe_write(tmp_path: Path):
    result = actions_for(tmp_path).write_file(
        "note.txt",
        "hello",
    )

    assert result.success is False
    assert "SAFE_WRITE" in result.error


def test_write_creates_file(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    actions = ProjectActionTools(tmp_path, permissions)
    result = actions.write_file("note.txt", "hello")

    assert result.success is True
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hello"


def test_write_does_not_overwrite_by_default(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    file_path = tmp_path / "note.txt"
    file_path.write_text("old", encoding="utf-8")

    result = ProjectActionTools(tmp_path, permissions).write_file(
        "note.txt",
        "new",
    )

    assert result.success is False
    assert file_path.read_text(encoding="utf-8") == "old"


def test_write_can_overwrite_with_explicit_flag(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    file_path = tmp_path / "note.txt"
    file_path.write_text("old", encoding="utf-8")

    result = ProjectActionTools(tmp_path, permissions).write_file(
        "note.txt",
        "new",
        overwrite=True,
    )

    assert result.success is True
    assert file_path.read_text(encoding="utf-8") == "new"


def test_write_rejects_workspace_escape(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    result = ProjectActionTools(tmp_path, permissions).write_file(
        "../outside.txt",
        "bad",
    )

    assert result.success is False
    assert "escapes" in result.error


def test_execute_requires_execute_permission(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python --version"
    )

    assert result.success is False
    assert "EXECUTE" in result.error


def test_execute_allows_pytest(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.EXECUTE)

    result = ProjectActionTools(
        Path(__file__).resolve().parents[1],
        permissions,
    ).execute_command(
        "python -m pytest -q tests/test_permissions.py"
    )

    assert result.success is True
    assert "passed" in result.output


def test_execute_rejects_shell_operators(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.EXECUTE)

    result = ProjectActionTools(tmp_path, permissions).execute_command(
        "python --version && whoami"
    )

    assert result.success is False
    assert "Shell operators" in result.error


def test_execute_rejects_destructive_git(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.EXECUTE)

    result = ProjectActionTools(tmp_path, permissions).execute_command(
        "git reset --hard"
    )

    assert result.success is False
    assert "not allowed" in result.error


def test_execute_rejects_arbitrary_python(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.EXECUTE)

    result = ProjectActionTools(tmp_path, permissions).execute_command(
        "python some_script.py"
    )

    assert result.success is False
    assert "limited to pytest" in result.error


def test_delete_requires_destructive_permission(tmp_path: Path):
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = actions_for(tmp_path).delete_file("note.txt")

    assert result.success is False
    assert "DESTRUCTIVE" in result.error
    assert file_path.exists()


def test_delete_file(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.DESTRUCTIVE)

    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = ProjectActionTools(
        tmp_path,
        permissions,
    ).delete_file("note.txt")

    assert result.success is True
    assert "Deleted" in result.output
    assert not file_path.exists()
