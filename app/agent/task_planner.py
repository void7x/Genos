from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TaskPlan:
    action: str
    target: str = ""
    details: str = ""
    permission: str = ""
    steps: tuple[str, ...] = ()


class TaskPlanner:
    """Deterministic natural-language task planner for Genos."""

    def plan(self, message: str) -> TaskPlan | None:
        text = " ".join(str(message).strip().split())
        lower = text.casefold()

        if not text:
            return None

        match = re.match(
            r"^(?:please\s+)?(?:create|make|write)\s+"
            r"(?:a\s+)?file\s+(?:called\s+|named\s+)?"
            r"(?P<target>\S+)"
            r"(?:\s+(?:with|containing|that\s+contains|having)\s+"
            r"(?P<details>.+))?$",
            text,
            re.IGNORECASE,
        )

        if match:
            target = match.group("target").strip("\"'")
            details = (match.group("details") or "").strip()

            if details:
                return TaskPlan(
                    action="create_file",
                    target=target,
                    details=details,
                    permission="SAFE_WRITE",
                    steps=(
                        f"Create {target}",
                        "Verify the file exists with the requested content",
                        "Remember the completed action",
                    ),
                )

            return TaskPlan(
                action="create_file",
                target=target,
                permission="SAFE_WRITE",
                steps=(
                    f"Create {target}",
                    "Confirm the intended file content",
                    "Verify the created file",
                    "Remember the completed action",
                ),
            )

        match = re.match(
            r"^(?:please\s+)?(?:create|add|write)\s+"
            r"(?:some\s+|new\s+)?tests?\s+"
            r"(?:for|covering)\s+(?P<target>.+)$",
            text,
            re.IGNORECASE,
        )

        if match:
            return TaskPlan(
                action="add_tests",
                target=match.group("target").strip(),
                permission="SAFE_WRITE",
                steps=(
                    "Inspect the target code",
                    "Create focused tests",
                    "Run the relevant test suite",
                    "Verify the result",
                    "Remember the completed action",
                ),
            )

        match = re.match(
            r"^(?:please\s+)?(?:add|enable|implement)\s+"
            r"(?:logging|logs)\s+(?:to|in|for)\s+(?P<target>.+)$",
            text,
            re.IGNORECASE,
        )

        if match:
            return TaskPlan(
                action="add_logging",
                target=match.group("target").strip(),
                permission="SAFE_WRITE",
                steps=(
                    "Inspect the target module",
                    "Add appropriate logging",
                    "Run focused tests",
                    "Verify the changes",
                    "Remember the completed action",
                ),
            )

        match = re.match(
            r"^(?:please\s+)?(?:fix|resolve|repair)\s+"
            r"(?:the\s+)?(?P<target>.+)$",
            text,
            re.IGNORECASE,
        )

        if match and any(
            marker in lower
            for marker in ("bug", "error", "issue", "failure", "problem")
        ):
            return TaskPlan(
                action="fix_bug",
                target=match.group("target").strip(),
                permission="SAFE_WRITE",
                steps=(
                    "Inspect the relevant code",
                    "Identify the cause",
                    "Apply a focused fix",
                    "Run the relevant tests",
                    "Verify the fix",
                    "Remember the completed action",
                ),
            )

        match = re.match(
            r"^(?:please\s+)?(?:refactor|restructure|clean\s+up)\s+"
            r"(?P<target>.+)$",
            text,
            re.IGNORECASE,
        )

        if match:
            return TaskPlan(
                action="refactor",
                target=match.group("target").strip(),
                permission="SAFE_WRITE",
                steps=(
                    "Inspect the target code",
                    "Plan the refactor",
                    "Apply the changes",
                    "Run the relevant tests",
                    "Verify behavior",
                    "Remember the completed action",
                ),
            )

        return None
