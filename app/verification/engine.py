from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.agent.test_failure_analyzer import TestFailureAnalyzer
from app.tools import ProjectActionTools, ProjectTools


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    summary: str
    checks: tuple[str, ...] = ()


class VerificationEngine:
    """Verify observable outcomes of Genos actions."""

    def __init__(
        self,
        workspace_path: str | Path,
        action_tools: ProjectActionTools | None = None,
    ):
        self.root = (
            Path(workspace_path)
            .expanduser()
            .resolve(strict=True)
        )

        if not self.root.is_dir():
            raise ValueError(
                f"Workspace is not a directory: {self.root}"
            )

        self.tools = ProjectTools(self.root)
        self.action_tools = action_tools

    def verify_file(
        self,
        relative_path: str,
        expected_content: str | None = None,
    ) -> VerificationResult:
        result = self.tools.read_file(relative_path)

        if not result.success:
            return VerificationResult(
                False,
                f"File verification failed: {result.error}",
                ("file exists and is readable",),
            )

        checks = ["file exists and is readable"]

        if expected_content is not None:
            if result.output != expected_content:
                return VerificationResult(
                    False,
                    f"File content mismatch: {relative_path}",
                    tuple(checks + ["expected content matches"]),
                )

            checks.append("expected content matches")

        return VerificationResult(
            True,
            f"Verified file: {relative_path}",
            tuple(checks),
        )

    def verify_git(self) -> VerificationResult:
        result = self.tools.git_status()

        if not result.success:
            return VerificationResult(
                False,
                f"Git verification failed: {result.error}",
                ("git status succeeded",),
            )

        if result.output:
            return VerificationResult(
                True,
                "Git verification complete: changes are present.",
                (
                    "git status succeeded",
                    "working tree inspected",
                    "changes detected",
                ),
            )

        return VerificationResult(
            True,
            "Git verification complete: working tree is clean.",
            (
                "git status succeeded",
                "working tree inspected",
                "working tree clean",
            ),
        )

    def verify_tests(self) -> VerificationResult:
        if self.action_tools is None:
            return VerificationResult(
                False,
                "Test verification is unavailable without execution tools.",
                ("execution tool configured",),
            )

        result = self.action_tools.execute_command(
            "python -m pytest -q"
        )

        if not result.success:
            details = result.error or result.output
            report = TestFailureAnalyzer().analyze(details)

            return VerificationResult(
                False,
                f"Test verification failed: {details}",
                (
                    "pytest command executed",
                    report.summary,
                ),
            )

        return VerificationResult(
            True,
            "Test verification passed.",
            (
                "pytest command executed",
                "pytest returned success",
            ),
        )

    def verify_project(self) -> VerificationResult:
        checks: list[str] = []

        info = self.tools.list_files()
        if info.success:
            checks.append("workspace is readable")
        else:
            return VerificationResult(
                False,
                f"Project verification failed: {info.error}",
                tuple(checks),
            )

        git = self.tools.git_status()
        if git.success:
            checks.append("git status succeeded")
        else:
            checks.append("git status unavailable")

        return VerificationResult(
            True,
            "Project verification passed.",
            tuple(checks),
        )
