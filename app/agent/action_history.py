from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ActionHistoryEntry:
    id: str
    workspace_id: str
    timestamp: str
    action: str
    target: str
    status: str
    verification: str
    recovery: str
    rollback: str
    summary: str


class ActionHistoryRepository:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workspace_id: str) -> Path:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        safe_name = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return self.root / safe_name / "history.json"

    def load(self, workspace_id: str) -> list[ActionHistoryEntry]:
        normalized_workspace = str(workspace_id).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized_workspace)

        if not path.exists():
            return []

        try:
            raw = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(raw, list):
            return []

        entries: list[ActionHistoryEntry] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            try:
                entry = ActionHistoryEntry(
                    id=str(item.get("id", "")),
                    workspace_id=str(
                        item.get("workspace_id", "")
                    ),
                    timestamp=str(
                        item.get("timestamp", "")
                    ),
                    action=str(item.get("action", "")),
                    target=str(item.get("target", "")),
                    status=str(item.get("status", "")),
                    verification=str(
                        item.get("verification", "")
                    ),
                    recovery=str(
                        item.get("recovery", "")
                    ),
                    rollback=str(
                        item.get("rollback", "")
                    ),
                    summary=str(
                        item.get("summary", "")
                    ),
                )
            except (TypeError, ValueError):
                continue

            if (
                entry.id
                and entry.workspace_id == normalized_workspace
                and entry.action
                and entry.target
            ):
                entries.append(entry)

        return entries

    def append(
        self,
        workspace_id: str,
        entry: ActionHistoryEntry,
    ) -> None:
        normalized_workspace = str(workspace_id).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized_workspace)
        path.parent.mkdir(parents=True, exist_ok=True)

        entries = self.load(normalized_workspace)
        entries.append(entry)

        path.write_text(
            json.dumps(
                [asdict(item) for item in entries],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


class ActionHistoryManager:
    def __init__(self, repository: ActionHistoryRepository):
        self.repository = repository

    def add(
        self,
        workspace_id: str,
        *,
        action: str,
        target: str,
        status: str,
        verification: str = "not-run",
        recovery: str = "not-needed",
        rollback: str = "not-needed",
        summary: str = "",
    ) -> ActionHistoryEntry:
        normalized_workspace = str(workspace_id).strip()
        normalized_action = str(action).strip()
        normalized_target = str(target).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        if not normalized_action:
            raise ValueError("Action cannot be empty.")

        if not normalized_target:
            raise ValueError("Target cannot be empty.")

        now = datetime.now(timezone.utc).isoformat()

        entry = ActionHistoryEntry(
            id=uuid.uuid4().hex[:16],
            workspace_id=normalized_workspace,
            timestamp=now,
            action=normalized_action,
            target=normalized_target,
            status=str(status).strip(),
            verification=str(
                verification
            ).strip(),
            recovery=str(recovery).strip(),
            rollback=str(rollback).strip(),
            summary=str(summary).strip(),
        )

        self.repository.append(
            normalized_workspace,
            entry,
        )

        return entry

    def list(
        self,
        workspace_id: str,
    ) -> list[ActionHistoryEntry]:
        return self.repository.load(workspace_id)
