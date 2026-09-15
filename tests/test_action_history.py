from pathlib import Path

import pytest

from app.agent.action_history import (
    ActionHistoryManager,
    ActionHistoryRepository,
)


def history_for(tmp_path: Path):
    return ActionHistoryManager(
        ActionHistoryRepository(
            tmp_path / "history"
        )
    )


def test_action_history_add_persists_entry(tmp_path: Path):
    history = history_for(tmp_path)

    entry = history.add(
        "workspace-test",
        action="edit",
        target="config.py",
        status="success",
        verification="passed",
        recovery="not-needed",
        rollback="not-needed",
        summary="Updated config.",
    )

    assert entry.action == "edit"
    assert entry.target == "config.py"
    assert entry.status == "success"

    loaded = history.list("workspace-test")

    assert len(loaded) == 1
    assert loaded[0] == entry


def test_action_history_is_append_only(tmp_path: Path):
    history = history_for(tmp_path)

    first = history.add(
        "workspace-test",
        action="write",
        target="a.txt",
        status="success",
    )

    second = history.add(
        "workspace-test",
        action="execute",
        target="pytest",
        status="failed",
        verification="failed",
    )

    loaded = history.list("workspace-test")

    assert [item.id for item in loaded] == [
        first.id,
        second.id,
    ]


def test_action_history_separates_workspaces(tmp_path: Path):
    history = history_for(tmp_path)

    history.add(
        "workspace-a",
        action="write",
        target="a.txt",
        status="success",
    )

    history.add(
        "workspace-b",
        action="write",
        target="b.txt",
        status="success",
    )

    assert len(history.list("workspace-a")) == 1
    assert history.list("workspace-a")[0].target == "a.txt"
    assert len(history.list("workspace-b")) == 1
    assert history.list("workspace-b")[0].target == "b.txt"


def test_action_history_rejects_empty_workspace(tmp_path: Path):
    history = history_for(tmp_path)

    with pytest.raises(
        ValueError,
        match="Workspace ID",
    ):
        history.add(
            "",
            action="write",
            target="a.txt",
            status="success",
        )


def test_action_history_rejects_empty_action(tmp_path: Path):
    history = history_for(tmp_path)

    with pytest.raises(
        ValueError,
        match="Action",
    ):
        history.add(
            "workspace-test",
            action="",
            target="a.txt",
            status="success",
        )
