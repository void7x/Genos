from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RollbackSnapshot:
    relative_path: str
    original_content: str


@dataclass(frozen=True)
class RollbackResult:
    success: bool
    summary: str


class RollbackManager:
    """Restore an existing workspace file from its captured pre-edit content."""

    def __init__(self, workspace_path: str | Path):
        self.root = Path(workspace_path).expanduser().resolve(strict=True)

        if not self.root.is_dir():
            raise ValueError(
                f"Workspace is not a directory: {self.root}"
            )

    def snapshot(
        self,
        relative_path: str,
        original_content: str,
    ) -> RollbackSnapshot:
        path = self._safe_path(relative_path)

        if not path.is_file():
            raise ValueError(
                f"Rollback requires an existing file: {relative_path}"
            )

        return RollbackSnapshot(
            relative_path=relative_path,
            original_content=original_content,
        )

    def restore(
        self,
        snapshot: RollbackSnapshot,
    ) -> RollbackResult:
        path = self._safe_path(snapshot.relative_path)

        if not path.is_file():
            return RollbackResult(
                False,
                f"Rollback failed: file not found: {snapshot.relative_path}",
            )

        try:
            path.write_text(
                snapshot.original_content,
                encoding="utf-8",
            )
        except OSError as exc:
            return RollbackResult(
                False,
                f"Rollback failed: {exc}",
            )

        try:
            restored = path.read_text(
                encoding="utf-8",
            )
        except OSError as exc:
            return RollbackResult(
                False,
                f"Rollback verification failed: {exc}",
            )

        if restored != snapshot.original_content:
            return RollbackResult(
                False,
                (
                    "Rollback verification failed: "
                    f"content mismatch in {snapshot.relative_path}"
                ),
            )

        return RollbackResult(
            True,
            f"Rollback restored: {snapshot.relative_path}",
        )

    def _safe_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)

        if candidate.is_absolute():
            raise ValueError(
                "Rollback paths must be relative to the workspace."
            )

        resolved = (self.root / candidate).resolve()

        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                "Rollback path escapes the active workspace."
            ) from exc

        return resolved
