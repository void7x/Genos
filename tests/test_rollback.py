from pathlib import Path

import pytest

from app.agent.rollback import RollbackManager


def test_rollback_snapshot_captures_original_content(tmp_path: Path):
    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    manager = RollbackManager(tmp_path)

    snapshot = manager.snapshot(
        "config.py",
        "old = True\n",
    )

    assert snapshot.relative_path == "config.py"
    assert snapshot.original_content == "old = True\n"


def test_rollback_restores_original_content(tmp_path: Path):
    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    manager = RollbackManager(tmp_path)
    snapshot = manager.snapshot(
        "config.py",
        "old = True\n",
    )

    target.write_text("new = False\n", encoding="utf-8")

    result = manager.restore(snapshot)

    assert result.success is True
    assert "Rollback restored" in result.summary
    assert target.read_text(encoding="utf-8") == "old = True\n"


def test_rollback_rejects_path_escape(tmp_path: Path):
    manager = RollbackManager(tmp_path)

    with pytest.raises(ValueError, match="escapes"):
        manager.snapshot(
            "../outside.py",
            "unsafe",
        )


def test_rollback_refuses_missing_file(tmp_path: Path):
    manager = RollbackManager(tmp_path)

    with pytest.raises(
        ValueError,
        match="existing file",
    ):
        manager.snapshot(
            "missing.py",
            "content",
        )


def test_rollback_detects_missing_target_during_restore(tmp_path: Path):
    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    manager = RollbackManager(tmp_path)
    snapshot = manager.snapshot(
        "config.py",
        "old = True\n",
    )

    target.unlink()

    result = manager.restore(snapshot)

    assert result.success is False
    assert "file not found" in result.summary
