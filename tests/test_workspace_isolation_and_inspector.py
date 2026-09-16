from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools
from app.workspace.inspector import ProjectInspector


def test_permissions_reset_when_active_workspace_changes(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    permissions = PermissionManager()
    ProjectActionTools(first, permissions)
    permissions.grant(PermissionLevel.SAFE_WRITE)
    assert permissions.is_allowed(PermissionLevel.SAFE_WRITE)

    ProjectActionTools(second, permissions)

    assert permissions.is_allowed(PermissionLevel.READ)
    assert not permissions.is_allowed(PermissionLevel.SAFE_WRITE)
    assert not permissions.is_allowed(PermissionLevel.EXECUTE)
    assert not permissions.is_allowed(PermissionLevel.DESTRUCTIVE)


def test_inspector_prunes_protected_directories(monkeypatch, tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "src").mkdir()
    (root / ".venv").mkdir()
    (root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    (root / ".venv" / "ignored.py").write_text("ignored", encoding="utf-8")

    original_walk = __import__("os").walk
    visited = []

    def tracking_walk(path):
        for current_root, directories, files in original_walk(path):
            if Path(current_root).resolve() == root.resolve():
                visited.append(tuple(directories))
            yield current_root, directories, files

    import app.workspace.inspector as inspector_module

    monkeypatch.setattr(inspector_module.os, "walk", tracking_walk)

    info = ProjectInspector().inspect(root)

    assert info.project_type == "Python"
    assert visited
    assert ".venv" not in visited[0]
