from __future__ import annotations

import re
from pathlib import Path


_FILE_PATTERN = re.compile(
    r"(?<![\w.-])"
    r"(?:[A-Za-z0-9_.-]+[\\/])*"
    r"[A-Za-z0-9_.-]+"
    r"\.(?:py|md|txt|json|yaml|yml|toml|ini|js|jsx|ts|tsx|css|html)"
    r"(?![\w.-])",
    re.IGNORECASE,
)


class ConversationContext:
    """Deterministic contextual reference resolver built from recent history."""

    def __init__(self, conversation):
        self.conversation = conversation

    def history(self) -> list[dict[str, str]]:
        return self.conversation.load()

    def previous_response(self) -> str:
        ignored = (
            "switched workspace.",
            "workspace attached and activated.",
        )

        for item in reversed(self.history()):
            if item.get("role") != "assistant":
                continue

            response = item.get("content", "").strip()

            if not response:
                continue

            if any(response.casefold().startswith(prefix) for prefix in ignored):
                continue

            return response

        return ""

    def _search_result_file(self) -> str:
        history = self.history()

        latest_search_terms: list[str] = []

        for item in reversed(history):
            if item.get("role") != "user":
                continue

            text = item.get("content", "").strip().casefold()

            if text.startswith("find "):
                latest_search_terms = re.findall(
                    r"[a-z0-9_]+",
                    text[5:],
                )
                break

            if text.startswith("search for "):
                latest_search_terms = re.findall(
                    r"[a-z0-9_]+",
                    text[11:],
                )
                break

            if text.startswith("search "):
                latest_search_terms = re.findall(
                    r"[a-z0-9_]+",
                    text[7:],
                )
                break

        candidates: list[str] = []

        for item in reversed(history):
            if item.get("role") != "assistant":
                continue

            content = item.get("content", "")

            for match in _FILE_PATTERN.findall(content):
                normalized = match.replace("\\", "/")

                if normalized not in candidates:
                    candidates.append(normalized)

        if not candidates:
            return ""

        meaningful_terms = [
            term
            for term in latest_search_terms
            if len(term) >= 4
        ]

        for candidate in candidates:
            stem = Path(candidate).stem.casefold()

            if any(term in stem or stem in term for term in meaningful_terms):
                return candidate

        return candidates[0]

    def last_file(self) -> str:
        return self._search_result_file()

    def resolve_file_reference(self, argument: str) -> str:
        text = " ".join(str(argument).strip().split()).casefold()

        references = {
            "that file",
            "this file",
            "the file",
            "the one you found",
            "the one you just found",
            "that one",
            "this one",
            "the main one",
            "main one",
            "the main file",
            "main file",
        }

        if text in references:
            return self.last_file()

        return argument.strip()

    def resolve_main_file(self) -> str:
        files = []

        for item in reversed(self.history()):
            if item.get("role") != "assistant":
                continue

            for match in _FILE_PATTERN.findall(item.get("content", "")):
                normalized = match.replace("\\", "/")

                if normalized not in files:
                    files.append(normalized)

        for candidate in files:
            if candidate.casefold().endswith("/main.py"):
                return candidate

            if candidate.casefold() == "main.py":
                return candidate

        return files[0] if files else ""

    def resolve_workspace_reference(self, argument: str) -> str:
        return argument.strip()
