"""Persistent recent conversation history for Mereum."""

from __future__ import annotations

import json
from pathlib import Path


class ConversationRepository:
    """Persist a bounded recent conversation as JSON."""

    def __init__(self, path: Path, max_messages: int = 100):
        self.path = Path(path)
        self.max_messages = max_messages

        if self.max_messages <= 0:
            raise ValueError("max_messages must be positive.")

    def load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw, list):
            return []

        history: list[dict[str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()

            if role not in {"user", "assistant"} or not content:
                continue

            history.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return history[-self.max_messages :]

    def save(self, history: list[dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        cleaned: list[dict[str, str]] = []

        for item in history:
            if not isinstance(item, dict):
                continue

            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()

            if role not in {"user", "assistant"} or not content:
                continue

            cleaned.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        cleaned = cleaned[-self.max_messages :]

        self.path.write_text(
            json.dumps(cleaned, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def append_turn(self, user_message: str, assistant_message: str) -> None:
        history = self.load()

        history.extend(
            [
                {
                    "role": "user",
                    "content": user_message.strip(),
                },
                {
                    "role": "assistant",
                    "content": assistant_message.strip(),
                },
            ]
        )

        self.save(history)
