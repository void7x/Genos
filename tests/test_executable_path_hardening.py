from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools


def actions_for(tmp_path: Path) -> ProjectActionTools:
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.EXECUTE)
    return ProjectActionTools(tmp_path, permissions)


def test_absolute_python_executable_path_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        'C:\\outside\\python.exe -m pytest -q'
    )

    assert result.success is False
    assert "executable path" in result.error.casefold()


def test_relative_python_executable_path_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        '.\\python.exe -m pytest -q'
    )

    assert result.success is False
    assert "executable path" in result.error.casefold()


def test_absolute_git_executable_path_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        'C:\\outside\\git.exe status'
    )

    assert result.success is False
    assert "executable path" in result.error.casefold()


def test_bare_allowed_executable_name_still_passes_allowlist(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        'python --version'
    )

    assert result.success is True
