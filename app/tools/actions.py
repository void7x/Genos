from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager

from .project_tools import ToolResult


class ProjectActionTools:
    """Permission-gated write and safe command execution tools."""

    _BLOCKED_DIRS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    }

    _ALLOWED_EXECUTABLES = {
        "python",
        "py",
        "pytest",
        "git",
    }

    _READ_ONLY_GIT_COMMANDS = {
        "status",
        "log",
        "diff",
        "branch",
        "rev-parse",
    }

    _BLOCKED_GIT_COMMANDS = {
        "commit",
        "push",
        "pull",
        "reset",
        "clean",
        "checkout",
        "restore",
        "rm",
        "rebase",
        "merge",
    }

    _SHELL_OPERATORS = ("&&", "||", "|", ";", ">", "<", "`", "$(")

    def __init__(
        self,
        workspace_path: str | Path,
        permissions: PermissionManager,
    ):
        self.root = Path(workspace_path).expanduser().resolve(strict=True)

        if not self.root.is_dir():
            raise ValueError(f"Workspace is not a directory: {self.root}")

        self.permissions = permissions

    def write_file(
        self,
        relative_path: str,
        content: str,
        *,
        overwrite: bool = False,
    ) -> ToolResult:
        try:
            self.permissions.require(PermissionLevel.SAFE_WRITE)
            target = self._safe_write_path(relative_path)
        except (PermissionError, ValueError) as exc:
            return ToolResult(False, "", str(exc))

        if target.exists() and not overwrite:
            return ToolResult(
                False,
                "",
                f"File already exists: {relative_path}",
            )

        data = str(content)
        if len(data.encode("utf-8")) > 1_000_000:
            return ToolResult(False, "", "File is too large (max 1 MB).")

        existed = target.exists()

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data, encoding="utf-8")
        except OSError as exc:
            return ToolResult(False, "", str(exc))

        action = "Overwrote" if existed else "Created"
        return ToolResult(
            True,
            f"{action}: {relative_path}",
        )

    def delete_file(self, relative_path: str) -> ToolResult:
        try:
            self.permissions.require(PermissionLevel.DESTRUCTIVE)
            target = self._safe_write_path(relative_path)
        except (PermissionError, ValueError) as exc:
            return ToolResult(False, "", str(exc))

        if not target.exists():
            return ToolResult(
                False,
                "",
                f"File not found: {relative_path}",
            )

        if not target.is_file():
            return ToolResult(
                False,
                "",
                f"Not a file: {relative_path}",
            )

        try:
            target.unlink()
        except OSError as exc:
            return ToolResult(False, "", str(exc))

        return ToolResult(True, f"Deleted: {relative_path}")

    def execute_command(self, command: str) -> ToolResult:
        try:
            self.permissions.require(PermissionLevel.EXECUTE)
        except PermissionError as exc:
            return ToolResult(False, "", str(exc))

        raw = str(command).strip()

        if not raw:
            return ToolResult(False, "", "Command cannot be empty.")

        if any(operator in raw for operator in self._SHELL_OPERATORS):
            return ToolResult(
                False,
                "",
                "Shell operators are not allowed.",
            )

        try:
            args = shlex.split(raw, posix=False)
        except ValueError as exc:
            return ToolResult(False, "", f"Invalid command syntax: {exc}")

        if not args:
            return ToolResult(False, "", "Command cannot be empty.")

        executable = Path(args[0].strip('"')).name.casefold()
        if executable.endswith(".exe"):
            executable = executable[:-4]

        if executable not in self._ALLOWED_EXECUTABLES:
            return ToolResult(
                False,
                "",
                f"Executable not allowed: {executable}",
            )

        if executable == "git":
            if len(args) < 2:
                return ToolResult(False, "", "Git subcommand is required.")

            subcommand = args[1].casefold()

            if subcommand in self._BLOCKED_GIT_COMMANDS:
                return ToolResult(
                    False,
                    "",
                    f"Git command not allowed: {subcommand}",
                )

            if subcommand not in self._READ_ONLY_GIT_COMMANDS:
                return ToolResult(
                    False,
                    "",
                    f"Git command not allowed: {subcommand}",
                )

        if executable in {"python", "py"}:
            normalized = [item.casefold() for item in args[1:]]

            is_pytest = (
                len(normalized) >= 2
                and normalized[0] == "-m"
                and normalized[1] == "pytest"
            )

            is_version = any(
                item in {"--version", "-v"}
                for item in normalized
            )

            if not is_pytest and not is_version:
                return ToolResult(
                    False,
                    "",
                    "Python execution is limited to pytest or version checks.",
                )

        try:
            result = subprocess.run(
                args,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ToolResult(False, "", str(exc))

        output = result.stdout.strip()
        error = result.stderr.strip()

        if len(output) > 20_000:
            output = output[:20_000] + "\n...[truncated]"

        if len(error) > 10_000:
            error = error[:10_000] + "\n...[truncated]"

        if result.returncode != 0:
            return ToolResult(
                False,
                output,
                error or f"Command exited with code {result.returncode}.",
            )

        return ToolResult(True, output, error)

    def _safe_write_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)

        if candidate.is_absolute():
            raise ValueError(
                "Write paths must be relative to the workspace."
            )

        resolved = (self.root / candidate).resolve()

        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                "Path escapes the active workspace."
            ) from exc

        parts = resolved.relative_to(self.root).parts

        if any(
            part.casefold() in self._BLOCKED_DIRS
            for part in parts
        ):
            raise ValueError(
                "Writing inside protected workspace directories is not allowed."
            )

        return resolved

