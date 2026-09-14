from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolResult:
    success: bool
    output: str
    error: str = ""


class ProjectTools:
    def __init__(self, workspace_path: str | Path):
        self.root = Path(workspace_path).expanduser().resolve(strict=True)

        if not self.root.is_dir():
            raise ValueError(f"Workspace is not a directory: {self.root}")

    def list_files(self, relative_path: str = ".") -> ToolResult:
        target = self._safe_path(relative_path)

        if not target.is_dir():
            return ToolResult(False, "", f"Not a directory: {relative_path}")

        entries = []

        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
            entries.append(
                f"{item.name}/" if item.is_dir() else item.name
            )

        return ToolResult(True, "\n".join(entries))

    def read_file(self, relative_path: str) -> ToolResult:
        target = self._safe_path(relative_path)

        if not target.is_file():
            return ToolResult(False, "", f"Not a file: {relative_path}")

        try:
            content = target.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            return ToolResult(False, "", str(exc))

        return ToolResult(True, content)

    def search_files(self, query: str) -> ToolResult:
        normalized = str(query).strip().casefold()

        if not normalized:
            return ToolResult(False, "", "Search query cannot be empty.")

        matches = []

        ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
        }

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            if any(part.casefold() in ignored_dirs for part in path.relative_to(self.root).parts):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            if normalized in content.casefold():
                relative = path.relative_to(self.root)
                matches.append(str(relative))

        return ToolResult(True, "\n".join(sorted(matches, key=str.casefold)))

    def git_status(self) -> ToolResult:
        return self._git("status", "--short")

    def git_log(self, limit: int = 10) -> ToolResult:
        if limit <= 0:
            return ToolResult(False, "", "Limit must be positive.")

        return self._git(
            "log",
            f"-{limit}",
            "--oneline",
        )

    def git_diff(self) -> ToolResult:
        return self._git("diff")

    def _git(self, *args: str) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ToolResult(False, "", str(exc))

        if result.returncode != 0:
            return ToolResult(
                False,
                result.stdout.strip(),
                result.stderr.strip(),
            )

        return ToolResult(True, result.stdout.strip())

    def _safe_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)

        if candidate.is_absolute():
            raise ValueError("Tool paths must be relative to the workspace.")

        resolved = (self.root / candidate).resolve()

        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                "Path escapes the active workspace."
            ) from exc

        return resolved
