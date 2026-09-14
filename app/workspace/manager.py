from __future__ import annotations

import hashlib
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import Workspace
from .repository import WorkspaceRepository


class WorkspaceManager:
    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    @staticmethod
    def validate(path: str | Path) -> Path:
        candidate = Path(path).expanduser()

        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(f"Workspace does not exist: {candidate}") from exc

        if not resolved.is_dir():
            raise ValueError(f"Workspace is not a directory: {resolved}")

        return resolved

    @staticmethod
    def _id(path: Path) -> str:
        value = str(path).casefold().encode("utf-8")
        return hashlib.sha256(value).hexdigest()[:16]

    @staticmethod
    def _is_git_repo(path: Path) -> bool:
        return (path / ".git").exists()

    def list(self) -> list[Workspace]:
        data = self.repository.load()
        result = []

        for item in data["workspaces"]:
            if not isinstance(item, dict):
                continue

            try:
                result.append(Workspace(**item))
            except TypeError:
                continue

        return result

    def current(self) -> Workspace | None:
        data = self.repository.load()
        current_id = data["current_id"]

        if not current_id:
            return None

        for workspace in self.list():
            if workspace.id == current_id:
                return workspace

        return None

    def attach(self, path: str | Path) -> Workspace:
        resolved = self.validate(path)
        workspace_id = self._id(resolved)
        now = datetime.now(timezone.utc).isoformat()

        data = self.repository.load()

        for index, item in enumerate(data["workspaces"]):
            if not isinstance(item, dict):
                continue

            if item.get("id") != workspace_id:
                continue

            workspace = Workspace(
                id=workspace_id,
                name=resolved.name or str(resolved),
                path=str(resolved),
                created_at=str(item.get("created_at") or now),
                last_opened_at=now,
                is_git_repo=self._is_git_repo(resolved),
            )

            data["workspaces"][index] = asdict(workspace)
            data["current_id"] = workspace_id
            self.repository.save(data)
            return workspace

        workspace = Workspace(
            id=workspace_id,
            name=resolved.name or str(resolved),
            path=str(resolved),
            created_at=now,
            last_opened_at=now,
            is_git_repo=self._is_git_repo(resolved),
        )

        data["workspaces"].append(asdict(workspace))
        data["current_id"] = workspace_id
        self.repository.save(data)

        return workspace

    def switch(self, workspace_id: str) -> Workspace:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        data = self.repository.load()

        for item in data["workspaces"]:
            if not isinstance(item, dict):
                continue

            if item.get("id") != normalized:
                continue

            resolved = self.validate(item.get("path", ""))
            now = datetime.now(timezone.utc).isoformat()

            workspace = Workspace(
                id=normalized,
                name=str(item.get("name") or resolved.name),
                path=str(resolved),
                created_at=str(item.get("created_at") or now),
                last_opened_at=now,
                is_git_repo=self._is_git_repo(resolved),
            )

            for index, candidate in enumerate(data["workspaces"]):
                if isinstance(candidate, dict) and candidate.get("id") == normalized:
                    data["workspaces"][index] = asdict(workspace)
                    break

            data["current_id"] = normalized
            self.repository.save(data)
            return workspace

        raise ValueError(f"Workspace not found: {normalized}")

    def detach(self) -> None:
        data = self.repository.load()
        data["current_id"] = None
        self.repository.save(data)
