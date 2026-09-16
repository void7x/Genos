from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.multi_step import MultiStepPlan


class WorkflowStateRepository:
    """Persist the pending multi-step workflow for a workspace."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workspace_id: str) -> Path:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        safe_name = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return self.root / safe_name / "workflow.json"

    def save(
        self,
        workspace_id: str,
        plan: MultiStepPlan,
    ) -> None:
        path = self._path(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                asdict(plan),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        workspace_id: str,
    ) -> MultiStepPlan | None:
        path = self._path(workspace_id)

        if not path.exists():
            return None

        try:
            raw = json.loads(
                path.read_text(encoding="utf-8")
            )

            if not isinstance(raw, dict):
                return None

            # Local import avoids a module-import cycle.
            from app.agent.multi_step import (
                MultiStep,
                MultiStepPlan,
            )

            raw_steps = raw.get("steps", [])
            if not isinstance(raw_steps, list):
                return None

            steps = tuple(
                MultiStep(**step)
                for step in raw_steps
                if isinstance(step, dict)
            )

            return MultiStepPlan(
                task_id=raw.get("task_id", ""),
                title=raw.get("title", ""),
                steps=steps,
                current_step=int(raw.get("current_step", 1)),
                status=str(raw.get("status", "pending")),
            )

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return None

    def clear(self, workspace_id: str) -> None:
        path = self._path(workspace_id)

        try:
            path.unlink()
        except FileNotFoundError:
            pass
