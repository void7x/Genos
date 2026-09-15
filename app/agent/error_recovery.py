from __future__ import annotations

from dataclasses import dataclass

from app.agent.test_failure_analyzer import TestFailureReport


@dataclass(frozen=True)
class RecoveryDecision:
    action: str
    reason: str
    safe: bool


class ErrorRecoveryEngine:
    """Choose a bounded, deterministic recovery action from failure evidence."""

    _TRANSIENT_SIGNALS = (
        "timed out",
        "timeout",
        "temporarily unavailable",
        "connection reset",
        "connection refused",
        "429",
        "503",
        "504",
    )

    def decide(
        self,
        report: TestFailureReport,
        raw_output: str = "",
    ) -> RecoveryDecision:
        text = str(raw_output or "").casefold()

        if not report.failed_tests and (
            "passed" in text
            or "no pytest failures detected" in report.summary.casefold()
        ):
            return RecoveryDecision(
                action="none",
                reason="No test failure requires recovery.",
                safe=True,
            )

        if any(
            signal in text
            for signal in self._TRANSIENT_SIGNALS
        ):
            return RecoveryDecision(
                action="retry_tests",
                reason=(
                    "The failure contains a transient execution signal; "
                    "a single bounded pytest retry is appropriate."
                ),
                safe=True,
            )

        if report.failed_tests:
            return RecoveryDecision(
                action="diagnose_failure",
                reason=(
                    "The failure appears deterministic; "
                    "automatic code changes are not justified."
                ),
                safe=False,
            )

        return RecoveryDecision(
            action="diagnose_failure",
            reason=(
                "A failure was reported, but it could not be classified "
                "as a safe transient condition."
            ),
            safe=False,
        )
