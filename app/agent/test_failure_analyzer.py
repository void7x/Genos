from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TestFailure:
    __test__ = False
    node: str
    file: str
    error: str


@dataclass(frozen=True)
class TestFailureReport:
    __test__ = False
    failed_tests: tuple[TestFailure, ...]
    summary: str


class TestFailureAnalyzer:
    """Parse pytest output into structured failure evidence."""

    _FAILED_PATTERN = re.compile(
        r"^(?P<node>[^ \t].*?::[^\s]+)\s+FAILED$",
        re.MULTILINE,
    )

    _PYTEST_SHORT_PATTERN = re.compile(
        r"^(?P<file>[^\s:]+\.py):\d+:.*?$",
        re.MULTILINE,
    )

    _ERROR_PATTERN = re.compile(
        r"^E\s+(?P<error>.+)$",
        re.MULTILINE,
    )

    def analyze(self, output: str) -> TestFailureReport:
        text = str(output or "")

        failed_nodes = [
            match.group("node").strip()
            for match in self._FAILED_PATTERN.finditer(text)
        ]

        failures: list[TestFailure] = []

        for node in failed_nodes:
            file = node.split("::", 1)[0]

            errors = [
                match.group("error").strip()
                for match in self._ERROR_PATTERN.finditer(text)
            ]

            error = (
                errors[0]
                if errors
                else self._extract_nearest_error(
                    text,
                    node,
                )
            )

            failures.append(
                TestFailure(
                    node=node,
                    file=file,
                    error=error,
                )
            )

        if failures:
            summary = (
                f"{len(failures)} test(s) failed: "
                + ", ".join(
                    failure.node
                    for failure in failures[:3]
                )
            )

            if len(failures) > 3:
                summary += (
                    f" and {len(failures) - 3} more"
                )

            return TestFailureReport(
                failed_tests=tuple(failures),
                summary=summary,
            )

        if "failed" in text.casefold():
            return TestFailureReport(
                failed_tests=(),
                summary=(
                    "Pytest reported a failure, but no "
                    "individual failed test node was parsed."
                ),
            )

        return TestFailureReport(
            failed_tests=(),
            summary="No pytest failures detected.",
        )

    @staticmethod
    def _extract_nearest_error(
        text: str,
        node: str,
    ) -> str:
        position = text.find(node)

        if position < 0:
            return ""

        tail = text[position:position + 2500]

        match = re.search(
            r"^E\s+(.+)$",
            tail,
            flags=re.MULTILINE,
        )

        if match:
            return match.group(1).strip()

        return ""
