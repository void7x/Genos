from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.tools import ProjectTools


@dataclass(frozen=True)
class PlanStep:
    tool: str
    argument: str = ""


@dataclass(frozen=True)
class AgentPlan:
    intent: str
    steps: tuple[PlanStep, ...]


class AgentOrchestrator:
    """Coordinate multiple local Genos tools for a single request."""

    def __init__(self, workspace_path: str | Path):
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

    def plan(self, request: str) -> AgentPlan | None:
        text = " ".join(
            str(request).strip().casefold().split()
        )

        if not text:
            return None

        if self._is_find_and_inspect(text):
            query = self._extract_inspection_query(request)

            if query:
                return AgentPlan(
                    intent="find_and_inspect",
                    steps=(
                        PlanStep("search_files", query),
                        PlanStep("read_relevant_files"),
                    ),
                )

        if self._is_project_diagnosis(text):
            return AgentPlan(
                intent="project_diagnosis",
                steps=(
                    PlanStep("project_info"),
                    PlanStep("git_status"),
                    PlanStep("list_files"),
                ),
            )

        if self._is_issue_diagnosis(text):
            query = self._extract_diagnosis_query(request)

            steps = [
                PlanStep("project_info"),
                PlanStep("git_status"),
                PlanStep("list_files"),
            ]

            if query:
                steps.append(PlanStep("search_files", query))

            return AgentPlan(
                intent="issue_diagnosis",
                steps=tuple(steps),
            )

        return None

    def run(self, request: str) -> str | None:
        plan = self.plan(request)

        if plan is None:
            return None

        if plan.intent == "find_and_inspect":
            return self._run_find_and_inspect(plan)

        if plan.intent == "project_diagnosis":
            return self._run_project_diagnosis()

        if plan.intent == "issue_diagnosis":
            return self._run_issue_diagnosis(plan)

        return None

    @staticmethod
    def _is_find_and_inspect(text: str) -> bool:
        has_search = any(
            marker in text
            for marker in (
                "find ",
                "search ",
                "locate ",
            )
        )

        has_inspection = any(
            marker in text
            for marker in (
                " explain",
                " inspect",
                " understand",
                "show me how",
                "show how",
            )
        )

        return has_search and has_inspection

    @staticmethod
    def _is_issue_diagnosis(text: str) -> bool:
        markers = (
            "why is this project failing",
            "why is the project failing",
            "why is this project broken",
            "what is wrong with this project",
            "what is wrong with the project",
            "find the problem with this project",
            "find the issue with this project",
            "diagnose the project",
            "diagnose this project",
            "find the likely cause",
            "what is wrong with",
            "why is",
            "why does this fail",
            "why does this error happen",
        )

        return any(marker in text for marker in markers)

    @staticmethod
    def _extract_diagnosis_query(request: str) -> str:
        original = " ".join(str(request).strip().split())
        text = original.casefold()

        prefixes = (
            "what is wrong with ",
            "find the problem with ",
            "find the issue with ",
            "what is the problem with ",
            "what is the issue with ",
            "why is ",
            "why does ",
            "find the likely cause of ",
            "diagnose ",
        )

        for prefix in prefixes:
            if text.startswith(prefix):
                value = original[len(prefix):].strip()

                if value.casefold() in {
                    "this project",
                    "the project",
                    "this",
                    "the project failing",
                    "this project failing",
                }:
                    return ""

                return value

        if (
            "why is this project failing" in text
            or "why is the project failing" in text
            or "why is this project broken" in text
            or "what is wrong with this project" in text
            or "what is wrong with the project" in text
        ):
            return ""

        keywords = (
            "authentication",
            "authorization",
            "login",
            "database",
            "api",
            "backend",
            "frontend",
            "tests",
            "testing",
            "docker",
            "build",
            "configuration",
            "config",
        )

        for keyword in keywords:
            if keyword in text:
                return keyword

        return ""
    @staticmethod
    def _is_project_diagnosis(text: str) -> bool:
        markers = (
            "diagnose this project",
            "analyze this project",
            "analyse this project",
            "give me a project overview",
            "give me an overview of this project",
            "check this project",
        )

        return any(marker in text for marker in markers)

    @staticmethod
    def _extract_inspection_query(request: str) -> str:
        original = " ".join(str(request).strip().split())
        text = original.casefold()

        prefixes = (
            "find where ",
            "search where ",
            "locate where ",
            "find and explain ",
            "find and inspect ",
            "find and understand ",
            "search and explain ",
            "search and inspect ",
            "search and understand ",
            "locate and explain ",
            "locate and inspect ",
            "locate and understand ",
            "find ",
            "search ",
            "locate ",
        )

        remainder = ""

        for prefix in prefixes:
            if text.startswith(prefix):
                remainder = original[len(prefix):].strip()
                break

        if not remainder:
            return ""

        endings = (
            " and explain it",
            " and explain",
            " and inspect it",
            " and inspect",
            " and understand it",
            " and understand",
        )

        for ending in endings:
            if remainder.casefold().endswith(ending):
                remainder = remainder[
                    : -len(ending)
                ].strip()
                break

        if text.startswith(("find where ", "search where ", "locate where ")):
            remainder = AgentOrchestrator._extract_where_subject(
                remainder
            )

        return remainder.strip(" .?!")

    @staticmethod
    def _extract_where_subject(text: str) -> str:
        normalized = text.strip()

        patterns = (
            r"^(.+?)\s+(?:is|are)\s+(?:handled|managed|implemented|located|defined)$",
            r"^(.+?)\s+(?:is|are)\s+handled$",
            r"^(.+?)\s+(?:is|are)\s+managed$",
            r"^(.+?)\s+(?:is|are)\s+implemented$",
        )

        for pattern in patterns:
            match = re.match(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return normalized

    def _run_find_and_inspect(
        self,
        plan: AgentPlan,
    ) -> str:
        search_step = next(
            step
            for step in plan.steps
            if step.tool == "search_files"
        )

        search = self.tools.search_files(
            search_step.argument
        )

        if not search.success:
            return f"Search failed: {search.error}"

        matches = [
            line.strip()
            for line in search.output.splitlines()
            if line.strip()
        ]

        if not matches:
            return (
                f"I searched for "
                f"'{search_step.argument}' "
                "but found no matching files."
            )
        prioritized = sorted(
            matches,
            key=lambda name: (
                0 if "permissions" in name.casefold() else 1,
                name.casefold(),
            ),
        )

        readable = []

        for relative_name in prioritized[:3]:
            result = self.tools.read_file(relative_name)

            if not result.success:
                readable.append(
                    f"[{relative_name}]\n"
                    f"Unable to read: {result.error}"
                )
                continue

            content = result.output

            if len(content) > 3000:
                content = (
                    content[:3000]
                    + "\n...[truncated]"
                )

            readable.append(
                f"[{relative_name}]\n{content}"
            )

        prioritized = sorted(
            matches,
            key=lambda name: (
                0
                if "permissions" in name.casefold()
                else 1,
                name.casefold(),
            ),
        )

        response = [
            f"I found {len(matches)} matching file(s).",
            f"Search: {search_step.argument}",
            "",
            "Relevant files:",
            *[
                f"- {name}"
                for name in prioritized[:3]
            ],
        ]

        if len(matches) > 3:
            response.append(
                f"- ...and {len(matches) - 3} more"
            )

        response.extend(
            [
                "",
                "I inspected the first relevant files:",
                "",
                "\n\n".join(readable),
            ]
        )

        return "\n".join(response)

    def _run_issue_diagnosis(self, plan: AgentPlan) -> str:
        from app.workspace import ProjectInspector

        info = ProjectInspector().inspect(self.root)
        git = self.tools.git_status()
        files = self.tools.list_files()

        query = ""
        for step in plan.steps:
            if step.tool == "search_files":
                query = step.argument
                break

        matches = self.tools.search_files(query) if query else None

        match_lines = []

        if matches is not None and matches.success:
            match_lines = [
                line.strip()
                for line in matches.output.splitlines()
                if line.strip()
            ]

        relevant = match_lines[:3]

        inspected = []

        for relative_path in relevant:
            result = self.tools.read_file(relative_path)

            inspected.append(
                {
                    "path": relative_path,
                    "content": (
                        result.output
                        if result.success
                        else ""
                    ),
                    "error": (
                        ""
                        if result.success
                        else result.error
                    ),
                }
            )

        test_evidence = self._collect_test_evidence(
            query,
            relevant,
        )

        causes = self._rank_root_causes(
            query=query,
            inspected=inspected,
            git=git.output if git.success else git.error,
        )

        lines = [
            "Project diagnosis:",
            f"Project: {info.name}",
            f"Type: {info.project_type}",
            f"Git branch: {info.git_branch or 'unknown'}",
            f"Git clean: {info.git_clean}",
            "",
            "Evidence:",
            (
                f"- Files discovered: "
                f"{len(files.output.splitlines()) if files.success else 0}"
            ),
            (
                "- Source directories: "
                f"{', '.join(info.source_dirs) if info.source_dirs else 'none detected'}"
            ),
            (
                "- Test directories: "
                f"{', '.join(info.test_dirs) if info.test_dirs else 'none detected'}"
            ),
            "",
            "Git status:",
            git.output if git.success else git.error,
        ]

        if query:
            lines.extend(
                [
                    "",
                    f"Relevant evidence for '{query}':",
                ]
            )

            if relevant:
                lines.extend(
                    f"- {item}"
                    for item in relevant
                )
            else:
                lines.append(
                    "- No directly matching files found."
                )

        lines.extend(
            [
                "",
                "Inspected evidence:",
                "",
            ]
        )

        if inspected:
            for item in inspected:
                lines.append(
                    f"[{item['path']}]"
                )

                if item["error"]:
                    lines.append(
                        f"Could not inspect file: {item['error']}"
                    )
                else:
                    lines.append(
                        item["content"][:1200].strip()
                    )

                lines.append("")
        else:
            lines.append(
                "- No matching files were available for inspection."
            )

        lines.extend(
            [
                "",
                "Test evidence:",
                "",
            ]
        )

        if test_evidence:
            for item in test_evidence:
                lines.extend(
                    [
                        f"[{item['path']}]",
                        item["content"][:1000].strip(),
                        "",
                    ]
                )
        else:
            lines.append(
                "- No directly related test evidence found."
            )

        lines.extend(
            [
                "Likely causes:",
            ]
        )

        if causes:
            for index, cause in enumerate(causes[:3], 1):
                lines.append(
                    f"{index}. {cause['title']} "
                    f"(confidence: {cause['confidence']})"
                )
                lines.append(
                    f"   Why: {cause['reason']}"
                )
        else:
            lines.append(
                "1. No strong root-cause signal was detected "
                "(confidence: low)"
            )
            lines.append(
                "   Why: available project evidence did not contain "
                "a specific failure signature."
            )

        lines.extend(
            [
                "",
                "Assessment:",
                (
                    "The diagnosis combines project structure, Git state, "
                    "source evidence, and related test evidence."
                ),
                "No files were modified.",
            ]
        )

        return "\n".join(lines)

    def _collect_test_evidence(
        self,
        query: str,
        relevant: list[str],
    ) -> list[dict[str, str]]:
        if not query:
            return []

        normalized_query = query.casefold()
        evidence = []

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

            relative = path.relative_to(self.root)

            if any(
                part.casefold() in ignored_dirs
                for part in relative.parts
            ):
                continue

            path_text = str(relative).casefold()

            if not (
                "test" in path_text
                or "tests" in path_text
            ):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            if normalized_query not in content.casefold():
                continue

            evidence.append(
                {
                    "path": str(relative),
                    "content": content,
                }
            )

            if len(evidence) >= 3:
                break

        return evidence
    @staticmethod
    def _rank_root_causes(
        query: str,
        inspected: list[dict[str, str]],
        git: str,
    ) -> list[dict[str, str]]:
        query_text = query.casefold()

        combined = "\n".join(
            item.get("content", "")
            for item in inspected
        ).casefold()

        causes = []

        def add(
            title: str,
            confidence: str,
            reason: str,
            score: int,
        ) -> None:
            causes.append(
                {
                    "title": title,
                    "confidence": confidence,
                    "reason": reason,
                    "score": score,
                }
            )

        auth_related = any(
            marker in query_text
            for marker in (
                "authentication",
                "authorization",
                "login",
                "auth",
            )
        )

        if auth_related:
            if any(
                marker in combined
                for marker in (
                    "401",
                    "unauthorized",
                    "invalid token",
                    "token expired",
                    "jwt",
                    "authorizationerror",
                )
            ):
                add(
                    "Authentication credentials or token validation",
                    "high",
                    (
                        "The inspected code contains authentication "
                        "failure signals such as 401/Unauthorized, "
                        "invalid-token handling, JWT validation, or an "
                        "authentication exception."
                    ),
                    100,
                )

            if any(
                marker in combined
                for marker in (
                    "os.getenv(",
                    "os.environ",
                    "environment.get",
                    "secret",
                    "client_secret",
                    "api_key",
                )
            ):
                add(
                    "Missing or misconfigured authentication configuration",
                    "high",
                    (
                        "The inspected code reads secrets or environment "
                        "configuration, making missing or incorrect "
                        "authentication configuration a plausible cause."
                    ),
                    90,
                )

            if any(
                marker in combined
                for marker in (
                    "oauth",
                    "openid",
                    "authorization_code",
                    "redirect_uri",
                    "callback",
                )
            ):
                add(
                    "Authentication flow or callback configuration",
                    "medium",
                    (
                        "The inspected code contains OAuth/OpenID-style "
                        "flow elements, so redirect, callback, or provider "
                        "configuration may be involved."
                    ),
                    75,
                )

        if any(
            marker in combined
            for marker in (
                "traceback",
                "exception",
                "raise ",
                "error",
                "failed",
            )
        ):
            add(
                "Unhandled exception or failure path",
                "medium",
                (
                    "The inspected code contains exception, error, or "
                    "failure signals that may explain the reported problem."
                ),
                60,
            )

        if any(
            marker in git.casefold()
            for marker in (
                "modified",
                "untracked",
                "conflict",
            )
        ):
            add(
                "Uncommitted or conflicting project state",
                "low",
                (
                    "Git reports local changes or conflicting repository "
                    "state, which can cause behavior to differ from the "
                    "expected version."
                ),
                40,
            )

        causes.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return [
            {
                "title": item["title"],
                "confidence": item["confidence"],
                "reason": item["reason"],
            }
            for item in causes
        ]
    def _run_project_diagnosis(self) -> str:
        from app.workspace import ProjectInspector

        info = ProjectInspector().inspect(self.root)
        status = self.tools.git_status()
        files = self.tools.list_files()

        return "\n".join(
            [
                "Project diagnosis:",
                "",
                f"Name: {info.name}",
                f"Type: {info.project_type}",
                (
                    "Languages: "
                    f"{', '.join(info.languages) or 'Unknown'}"
                ),
                (
                    "Frameworks: "
                    f"{', '.join(info.frameworks) or 'None detected'}"
                ),
                f"Git branch: {info.git_branch or 'Unknown'}",
                "",
                "Git status:",
                (
                    status.output
                    if status.output
                    else "Working tree clean."
                ),
                "",
                "Top-level files/directories:",
                files.output if files.success else files.error,
            ]
        )















