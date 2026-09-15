from app.agent.test_failure_analyzer import TestFailureAnalyzer


def test_analyzer_extracts_failed_test():
    output = """
============================= test session starts =============================
tests/test_auth.py::test_login FAILED
E   AssertionError: expected token
=========================== short test summary info ============================
FAILED tests/test_auth.py::test_login - AssertionError
1 failed, 4 passed in 0.42s
"""

    report = TestFailureAnalyzer().analyze(output)

    assert len(report.failed_tests) == 1
    assert report.failed_tests[0].node == "tests/test_auth.py::test_login"
    assert report.failed_tests[0].file == "tests/test_auth.py"
    assert "AssertionError" in report.failed_tests[0].error
    assert "1 test(s) failed" in report.summary


def test_analyzer_handles_multiple_failures():
    output = """
tests/test_auth.py::test_login FAILED
tests/test_api.py::test_request FAILED
E   ValueError: invalid token
2 failed
"""

    report = TestFailureAnalyzer().analyze(output)

    assert len(report.failed_tests) == 2
    assert report.failed_tests[0].file == "tests/test_auth.py"
    assert report.failed_tests[1].file == "tests/test_api.py"


def test_analyzer_handles_no_failures():
    output = """
========================= 12 passed in 0.50s =========================
"""

    report = TestFailureAnalyzer().analyze(output)

    assert report.failed_tests == ()
    assert report.summary == "No pytest failures detected."


def test_analyzer_handles_unparsed_failure():
    output = "pytest stopped unexpectedly: failed"

    report = TestFailureAnalyzer().analyze(output)

    assert report.failed_tests == ()
    assert "failure" in report.summary.casefold()
