from pathlib import Path

from app.memory import MemoryManager, MemoryRepository


def manager_for(tmp_path: Path) -> MemoryManager:
    return MemoryManager(
        MemoryRepository(tmp_path / "workspaces")
    )


def test_memory_is_scoped_to_workspace(tmp_path):
    manager = manager_for(tmp_path)

    first = manager.add("workspace-a", "Uses Python", ("stack",))
    second = manager.add("workspace-b", "Uses Python", ("stack",))

    assert first.workspace_id == "workspace-a"
    assert second.workspace_id == "workspace-b"

    assert manager.list("workspace-a") == [first]
    assert manager.list("workspace-b") == [second]


def test_duplicate_memory_is_not_added_twice(tmp_path):
    manager = manager_for(tmp_path)

    first = manager.add("workspace-a", "Uses Python")
    second = manager.add("workspace-a", "Uses Python")

    assert second == first
    assert len(manager.list("workspace-a")) == 1


def test_memory_persists_across_manager_instances(tmp_path):
    repository = MemoryRepository(tmp_path / "workspaces")

    first = MemoryManager(repository)
    memory = first.add("workspace-a", "Runs with pytest", ("testing",))

    second = MemoryManager(
        MemoryRepository(tmp_path / "workspaces")
    )

    assert second.list("workspace-a") == [memory]


def test_memory_search_is_workspace_scoped(tmp_path):
    manager = manager_for(tmp_path)

    manager.add("workspace-a", "Frontend uses React", ("frontend",))
    manager.add("workspace-b", "Frontend uses Vue", ("frontend",))

    result = manager.search("workspace-a", "React")

    assert len(result) == 1
    assert result[0].content == "Frontend uses React"


def test_memory_search_ranks_matching_terms(tmp_path):
    manager = manager_for(tmp_path)

    manager.add("workspace-a", "Python backend uses FastAPI")
    manager.add("workspace-a", "Python project")
    manager.add("workspace-a", "Frontend uses React")

    result = manager.search("workspace-a", "Python FastAPI")

    assert result[0].content == "Python backend uses FastAPI"
    assert result[1].content == "Python project"


def test_delete_memory(tmp_path):
    manager = manager_for(tmp_path)

    memory = manager.add("workspace-a", "Uses Git")

    assert manager.delete("workspace-a", memory.id) is True
    assert manager.list("workspace-a") == []
    assert manager.delete("workspace-a", memory.id) is False


def test_empty_memory_is_rejected(tmp_path):
    manager = manager_for(tmp_path)

    try:
        manager.add("workspace-a", "   ")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_empty_workspace_is_rejected(tmp_path):
    manager = manager_for(tmp_path)

    try:
        manager.add("   ", "Uses Python")
    except ValueError as exc:
        assert "Workspace ID" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

def test_memory_search_uses_tags_for_relevance(tmp_path):
    manager = manager_for(tmp_path)

    manager.add(
        "workspace-a",
        "The service starts normally",
        ("authentication", "security"),
    )
    manager.add(
        "workspace-a",
        "Authentication uses tokens",
        ("api",),
    )

    result = manager.search(
        "workspace-a",
        "authentication",
    )

    assert result[0].content == "The service starts normally"


def test_memory_search_returns_strongest_match_first(tmp_path):
    manager = manager_for(tmp_path)

    manager.add(
        "workspace-a",
        "Python backend service",
        ("stack",),
    )
    manager.add(
        "workspace-a",
        "Authentication service",
        ("authentication", "security"),
    )

    result = manager.search(
        "workspace-a",
        "authentication security",
    )

    assert result[0].content == "Authentication service"
