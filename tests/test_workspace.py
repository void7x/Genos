from pathlib import Path

import pytest

from app.workspace import WorkspaceManager, WorkspaceRepository


def manager_for(tmp_path: Path) -> WorkspaceManager:
    return WorkspaceManager(
        WorkspaceRepository(tmp_path / "workspaces.json")
    )


def test_attach_creates_and_persists_workspace(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manager = manager_for(tmp_path)

    workspace = manager.attach(project)

    assert workspace.name == "project"
    assert workspace.path == str(project.resolve())
    assert manager.current() == workspace
    assert len(manager.list()) == 1


def test_attach_same_workspace_does_not_duplicate(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manager = manager_for(tmp_path)

    first = manager.attach(project)
    second = manager.attach(project)

    assert first.id == second.id
    assert len(manager.list()) == 1


def test_attach_rejects_missing_workspace(tmp_path):
    manager = manager_for(tmp_path)

    with pytest.raises(ValueError, match="does not exist"):
        manager.attach(tmp_path / "missing")


def test_attach_rejects_file(tmp_path):
    file_path = tmp_path / "project.txt"
    file_path.write_text("x", encoding="utf-8")
    manager = manager_for(tmp_path)

    with pytest.raises(ValueError, match="not a directory"):
        manager.attach(file_path)


def test_switch_changes_current_workspace(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    manager = manager_for(tmp_path)

    one = manager.attach(first)
    two = manager.attach(second)

    assert manager.current().id == two.id

    switched = manager.switch(one.id)

    assert switched.id == one.id
    assert manager.current().id == one.id
    assert len(manager.list()) == 2


def test_detach_clears_current_but_keeps_workspace(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    manager = manager_for(tmp_path)

    manager.attach(project)
    manager.detach()

    assert manager.current() is None
    assert len(manager.list()) == 1


def test_workspace_state_survives_new_manager_instance(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    first = manager_for(tmp_path)
    workspace = first.attach(project)

    second = manager_for(tmp_path)

    assert second.current().id == workspace.id
    assert second.current().path == workspace.path


def test_git_workspace_is_detected(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()

    manager = manager_for(tmp_path)
    workspace = manager.attach(project)

    assert workspace.is_git_repo is True
