from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools


def actions_for(tmp_path: Path) -> ProjectActionTools:
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)
    permissions.grant(PermissionLevel.EXECUTE)
    permissions.grant(PermissionLevel.DESTRUCTIVE)
    return ProjectActionTools(tmp_path, permissions)


def test_git_cannot_redirect_repository_outside_workspace(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "git --git-dir C:\\outside\\.git status"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_git_cannot_redirect_worktree_outside_workspace(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "git --work-tree C:\\outside status"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_pytest_absolute_target_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q C:\\outside\\test.py"
    )

    assert result.success is False
    assert "workspace" in result.error.casefold()


def test_pytest_parent_traversal_target_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q ..\\outside\\test.py"
    )

    assert result.success is False
    assert "workspace" in result.error.casefold()


def test_protected_directory_write_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).write_file(
        ".git\\malicious.txt",
        "bad",
    )

    assert result.success is False
    assert "protected" in result.error.casefold()


def test_protected_directory_delete_is_rejected(tmp_path: Path):
    protected = tmp_path / ".venv"
    protected.mkdir()
    target = protected / "secret.txt"
    target.write_text("secret", encoding="utf-8")

    result = actions_for(tmp_path).delete_file(
        ".venv\\secret.txt"
    )

    assert result.success is False
    assert target.exists()


def test_unknown_executable_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "cmd.exe /c whoami"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_shell_command_substitution_is_rejected(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest $(whoami)"
    )

    assert result.success is False
    assert "shell operators" in result.error.casefold()


def test_command_output_does_not_allow_arbitrary_python(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -c \"print('owned')\""
    )

    assert result.success is False
    assert "pytest" in result.error.casefold()
from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools


def actions_for(tmp_path: Path) -> ProjectActionTools:
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)
    permissions.grant(PermissionLevel.EXECUTE)
    permissions.grant(PermissionLevel.DESTRUCTIVE)
    return ProjectActionTools(tmp_path, permissions)


def test_git_cannot_use_c_directory_override(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "git -C C:\\outside status"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_git_cannot_use_equals_path_override(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "git --git-dir=C:\\outside\\.git status"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_pytest_cannot_load_config_outside_workspace(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q -c C:\\outside\\pytest.ini"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_pytest_cannot_set_external_rootdir(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q --rootdir C:\\outside"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_pytest_cannot_set_external_basetemp(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q --basetemp C:\\outside\\temp"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_pytest_plugin_loading_is_blocked(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q -p malicious_plugin"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()


def test_python_environment_module_override_is_not_allowed(tmp_path: Path):
    result = actions_for(tmp_path).execute_command(
        "python -m pytest -q --confcutdir C:\\outside"
    )

    assert result.success is False
    assert "not allowed" in result.error.casefold()
