from pathlib import Path

import pytest

from app.memory import MemoryManager, MemoryRepository


def manager_for(tmp_path: Path) -> MemoryManager:
    return MemoryManager(
        MemoryRepository(tmp_path / "workspaces")
    )


def test_memory_allows_normal_and_arbitrary_workspace_ids_safely(tmp_path):
    manager = manager_for(tmp_path)

    normal = manager.add("workspace-a", "Uses Python")
    nested = manager.add("../outside", "Must remain scoped")

    assert normal.workspace_id == "workspace-a"
    assert nested.workspace_id == "../outside"

    assert manager.list("workspace-a") == [normal]
    assert manager.list("../outside") == [nested]

    assert not (tmp_path / "outside").exists()


def test_memory_rejects_empty_workspace_id(tmp_path):
    manager = manager_for(tmp_path)

    with pytest.raises(ValueError, match="Workspace ID cannot be empty"):
        manager.list("")

    with pytest.raises(ValueError, match="Workspace ID cannot be empty"):
        manager.add("   ", "Uses Python")
