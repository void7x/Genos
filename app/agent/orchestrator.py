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

        return None

    def run(self, request: str) -> str | None:
        plan = self.plan(request)

        if plan is None:
            return None

        if plan.intent == "find_and_inspect":
            return self._run_find_and_inspect(plan)

        if plan.intent == "project_diagnosis":
            return self._run_project_diagnosis()

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

