from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    argument: str = ""


class IntentRouter:
    """Deterministic natural-language intent router for Genos."""

    def route(self, message: str) -> Intent:
        original = " ".join(str(message).strip().split())
        text = original.casefold()

        if not text:
            return Intent("empty")

        if text in {"exit", "quit", "bye", "goodbye"}:
            return Intent("exit")

        if text in {"approve", "yes, approve", "continue"}:
            return Intent("approve")

        if text in {"deny", "cancel", "no, cancel", "stop"}:
            return Intent("deny")

        if text in {"help", "?", "commands"}:
            return Intent("help")

        if text in {"hi", "hello", "hey", "hey genos"}:
            return Intent("hello")

        if any(
            phrase in text
            for phrase in (
                "what features",
                "what can you do",
                "what do you do",
                "what are your features",
                "show your features",
                "what capabilities",
                "your capabilities",
                "what can genos do",
            )
        ):
            return Intent("capabilities")

        if any(
            phrase in text
            for phrase in (
                "what is this project",
                "tell me about this project",
                "describe this project",
                "explain this project",
            )
        ) or text in {"project", "project info", "project details"}:
            return Intent("project_info")

        if any(
            phrase in text
            for phrase in (
                "list files",
                "show files",
                "show me the files",
                "show me the project files",
                "what files are here",
                "what files do we have",
                "show project files",
                "show me what files you have",
            )
        ) or text == "files":
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

        if text in {"readme", "show readme", "show the readme"}:
            return Intent("read_file", "README.md")

        if "read the readme" in text or "readme file" in text:
            return Intent("read_file", "README.md")

        if text.startswith("find "):
            return Intent("find", original[len("find "):].strip())

        if text.startswith("search for "):
            return Intent(
                "find",
                original[len("search for "):].strip(),
            )

        if text.startswith("search "):
            return Intent(
                "find",
                original[len("search "):].strip(),
            )

        if any(
            phrase in text
            for phrase in (
                "git status",
                "git changes",
                "uncommitted changes",
                "working tree",
                "repository status",
                "are there changes",
                "did anything change",
                "is the repository clean",
            )
        ):
            return Intent("git_status")

        if any(
            phrase in text
            for phrase in (
                "git log",
                "commit history",
                "recent commits",
                "show commits",
                "what changed recently",
            )
        ):
            return Intent("git_log")

        if (
            text in {"goals", "show goals", "my goals"}
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
            or "what can i modify" in text
        ):
            return Intent("permissions")

        # Permission: SAFE_WRITE
        if any(
            phrase in text
            for phrase in (
                "grant safe write",
                "give safe write",
                "give me safe write",
                "allow safe write",
                "enable safe write",
                "let me modify files",
                "let me edit files",
                "give me permission to modify files",
                "give me permission to edit files",
                "allow me to modify files",
                "allow me to edit files",
                "enable file editing",
                "enable file modification",
                "you can modify files now",
                "you can edit files now",
            )
        ):
            return Intent("grant_safe_write")

        # Permission: EXECUTE
        if any(
            phrase in text
            for phrase in (
                "grant execute",
                "give execute",
                "give me execute",
                "allow execute",
                "enable execute",
                "let me execute commands",
                "let me run commands",
                "give me permission to execute",
                "give me permission to run commands",
                "allow me to execute commands",
                "allow me to run commands",
                "enable command execution",
            )
        ):
            return Intent("grant_execute")

        # Permission: DESTRUCTIVE
        if any(
            phrase in text
            for phrase in (
                "grant destructive",
                "give destructive",
                "give me destructive",
                "allow destructive",
                "enable destructive",
                "let me delete files",
                "give me permission to delete files",
                "allow me to delete files",
                "enable deletion",
            )
        ):
            return Intent("grant_destructive")

        # Permission revocation
        if any(
            phrase in text
            for phrase in (
                "revoke safe write",
                "remove safe write",
                "disable safe write",
                "take away file modification permission",
            )
        ):
            return Intent("revoke_safe_write")

        if any(
            phrase in text
            for phrase in (
                "revoke execute",
                "remove execute",
                "disable execute",
                "take away execute permission",
            )
        ):
            return Intent("revoke_execute")

        if any(
            phrase in text
            for phrase in (
                "revoke destructive",
                "remove destructive",
                "disable destructive",
                "take away delete permission",
            )
        ):
            return Intent("revoke_destructive")

        # Workspace discovery/switching
        if any(
            phrase in text
            for phrase in (
                "list workspaces",
                "list my workspaces",
                "show workspaces",
                "show my workspaces",
                "what projects do you know",
                "what projects do you have",
                "what projects are available",
            )
        ):
            return Intent("workspace_list")

        for prefix in (
            "switch to ",
            "go to ",
            "open ",
            "use ",
            "move to ",
            "work on ",
            "open project ",
            "switch project to ",
        ):
            if text.startswith(prefix):
                return Intent(
                    "workspace_switch",
                    original[len(prefix):].strip().strip('"'),
                )

        # Natural delete
        for prefix in (
            "delete file ",
            "remove file ",
            "delete ",
            "remove ",
        ):
            if text.startswith(prefix):
                return Intent(
                    "delete_file",
                    original[len(prefix):].strip(),
                )

        # Natural command execution
        if text in {
            "run tests",
            "run the tests",
            "execute tests",
            "test the project",
        }:
            return Intent("run_tests")

        # Natural verification
        if text in {
            "verify project",
            "verify this project",
            "check my project",
            "verify the project",
        }:
            return Intent("verify_project")

        if text in {
            "verify git",
            "verify git status",
            "verify repository",
        }:
            return Intent("verify_git")

        if text in {
            "verify tests",
            "verify test suite",
            "verify the tests",
        }:
            return Intent("verify_tests")

        if text.startswith("verify file "):
            return Intent(
                "verify_file",
                original[len("verify file "):].strip(),
            )

        # Natural task: create status notes
        if (
            "create a notes file" in text
            or "create notes file" in text
            or "make a notes file" in text
            or "make notes file" in text
        ) and "project status" in text:
            return Intent("natural_project_status")

        return Intent("unknown")
