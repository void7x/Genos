from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    argument: str = ""


class IntentRouter:
    """Map natural-language requests to Genos v1 capabilities."""

    def route(self, message: str) -> Intent:
        original = " ".join(str(message).strip().split())
        text = original.casefold()

        if not text:
            return Intent("empty")

        if text in {"exit", "quit", "bye", "goodbye"}:
            return Intent("exit")

        if text in {"help", "?", "commands"}:
            return Intent("help")

        if text in {"hi", "hello", "hey", "hey genos"}:
            return Intent("hello")

        if (
            "what features" in text
            or "what can you do" in text
            or "what do you do" in text
            or "what are your features" in text
            or "show your features" in text
            or "what capabilities" in text
            or "your capabilities" in text
        ):
            return Intent("capabilities")

        if (
            "what is this project" in text
            or "tell me about this project" in text
            or "describe this project" in text
            or "explain this project" in text
            or text in {
                "project",
                "project info",
                "project details",
            }
        ):
            return Intent("project_info")

        if (
            "list files" in text
            or "show files" in text
            or "show me the files" in text
            or "show me the project files" in text
            or "what files are here" in text
            or "what files do we have" in text
            or "show project files" in text
            or text == "files"
        ):
            return Intent("list_files")

        if text.startswith("list files in "):
            return Intent(
                "list_files",
                original[len("list files in "):].strip(),
            )

        if text.startswith("show files in "):
            return Intent(
                "list_files",
                original[len("show files in "):].strip(),
            )

        if text.startswith("read file "):
            return Intent(
                "read_file",
                original[len("read file "):].strip(),
            )

        if text.startswith("read "):
            argument = original[len("read "):].strip()

            if argument.casefold() in {
                "readme",
                "the readme",
                "readme file",
            }:
                return Intent("read_file", "README.md")

            return Intent("read_file", argument)

        if (
            text in {
                "readme",
                "show readme",
                "show the readme",
            }
            or "read the readme" in text
            or "readme file" in text
        ):
            return Intent("read_file", "README.md")

        if text.startswith("find "):
            return Intent(
                "find",
                original[len("find "):].strip(),
            )

        if text.startswith("search for "):
            prefix = "search for "
            return Intent(
                "find",
                original[len(prefix):].strip(),
            )

        if text.startswith("search "):
            return Intent(
                "find",
                original[len("search "):].strip(),
            )

        if (
            "git status" in text
            or "git changes" in text
            or "uncommitted changes" in text
            or "working tree" in text
            or "repository status" in text
        ):
            return Intent("git_status")

        if (
            "git log" in text
            or "commit history" in text
            or "recent commits" in text
            or "show commits" in text
        ):
            return Intent("git_log")

        if (
            text in {
                "goals",
                "show goals",
                "my goals",
            }
            or "what are my goals" in text
            or "what goals do i have" in text
            or "show my goals" in text
            or "project goals" in text
        ):
            return Intent("goals")

        if text.startswith("search memory "):
            return Intent(
                "memory",
                original[len("search memory "):].strip(),
            )

        if text.startswith("memory "):
            return Intent(
                "memory",
                original[len("memory "):].strip(),
            )

        if text.startswith("remember "):
            return Intent(
                "remember",
                original[len("remember "):].strip(),
            )

        if text.startswith("goal "):
            return Intent(
                "goal",
                original[len("goal "):].strip(),
            )

        if (
            text in {
                "permissions",
                "permission",
                "show permissions",
            }
            or "what permissions" in text
            or "what am i allowed to do" in text
            or "what can you modify" in text
            or "what access do you have" in text
        ):
            return Intent("permissions")

        return Intent("unknown")
