from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Workspace:
    id: str
    name: str
    path: str
    created_at: str
    last_opened_at: str
    is_git_repo: bool
