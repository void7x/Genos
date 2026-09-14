from __future__ import annotations

import json
from pathlib import Path


class WorkspaceRepository:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {"current_id": None, "workspaces": []}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"current_id": None, "workspaces": []}

        if not isinstance(data, dict):
            return {"current_id": None, "workspaces": []}

        workspaces = data.get("workspaces")
        current_id = data.get("current_id")

        if not isinstance(workspaces, list):
            workspaces = []

        if current_id is not None and not isinstance(current_id, str):
            current_id = None

        return {
            "current_id": current_id,
            "workspaces": workspaces,
        }

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
