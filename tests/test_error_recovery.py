from app.agent.error_recovery import ErrorRecoveryEngine
from app.agent.test_failure_analyzer import TestFailureAnalyzer


def test_recovery_recommends_retry_for_timeout():
    output = (
        "pytest timed out while collecting tests\n"
        "1 failed"
    )

    report = TestFailureAnalyzer().analyze(output)
    decision = ErrorRecoveryEngine().decide(report, output)

    assert decision.action == "retry_tests"
    assert decision.safe is True


def test_recovery_recommends_retry_for_service_unavailable():
    output = (
        "backend temporarily unavailable (503)\n"
        "pytest failed"
    )

    report = TestFailureAnalyzer().analyze(output)
    decision = ErrorRecoveryEngine().decide(report, output)

    assert decision.action == "retry_tests"
    assert decision.safe is True


def test_recovery_does_not_auto_fix_deterministic_failure():
    output = (
        "tests/test_auth.py::test_login FAILED\n"
        "E   AssertionError: expected token\n"
        "1 failed"
    )

    report = TestFailureAnalyzer().analyze(output)
    decision = ErrorRecoveryEngine().decide(report, output)

    assert decision.action == "diagnose_failure"
    assert decision.safe is False


def test_recovery_handles_unparsed_failure():
    output = "pytest stopped unexpectedly: failed"

    report = TestFailureAnalyzer().analyze(output)
    decision = ErrorRecoveryEngine().decide(report, output)

    assert decision.action == "diagnose_failure"
    assert decision.safe is False


def test_recovery_returns_none_for_success():
    output = "================ 196 passed in 88.80s ================"

    report = TestFailureAnalyzer().analyze(output)
    decision = ErrorRecoveryEngine().decide(report, output)

    assert decision.action == "none"
    assert decision.safe is True
