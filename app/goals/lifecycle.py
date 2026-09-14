"""Structured intent for changing an existing Genos goal."""

from __future__ import annotations

from dataclasses import dataclass

GOAL_ACTIONS = {
    "complete",
    "pause",
    "resume",
    "cancel",
}


@dataclass(frozen=True)
class GoalLifecycleIntent:
    action: str
    goal_title: str

    def __post_init__(self) -> None:
        action = self.action.strip().lower()
        goal_title = " ".join(self.goal_title.strip().split())

        if action not in GOAL_ACTIONS:
            raise ValueError(f"Unsupported goal action: {action}")

        if not goal_title:
            raise ValueError("Goal title cannot be empty.")

        object.__setattr__(self, "action", action)
        object.__setattr__(self, "goal_title", goal_title)
