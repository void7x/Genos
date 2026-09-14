from app.agent.task_planner import TaskPlanner


def test_create_file_task_extracts_target_and_content():
    plan = TaskPlanner().plan(
        "Create a file called config.py containing PORT = 8000"
    )

    assert plan is not None
    assert plan.action == "create_file"
    assert plan.target == "config.py"
    assert plan.details == "PORT = 8000"
    assert plan.permission == "SAFE_WRITE"


def test_create_file_without_content_requests_details():
    plan = TaskPlanner().plan("make a file named config.py")

    assert plan is not None
    assert plan.action == "create_file"
    assert plan.target == "config.py"
    assert plan.details == ""
    assert plan.permission == "SAFE_WRITE"


def test_add_tests_task():
    plan = TaskPlanner().plan(
        "create tests for the authentication module"
    )

    assert plan is not None
    assert plan.action == "add_tests"
    assert plan.target == "the authentication module"
    assert plan.permission == "SAFE_WRITE"


def test_logging_task():
    plan = TaskPlanner().plan(
        "add logging to the authentication module"
    )

    assert plan is not None
    assert plan.action == "add_logging"
    assert plan.target == "the authentication module"
    assert plan.permission == "SAFE_WRITE"


def test_bug_fix_task():
    plan = TaskPlanner().plan(
        "fix the authentication bug"
    )

    assert plan is not None
    assert plan.action == "fix_bug"
    assert plan.target == "authentication bug"
    assert plan.permission == "SAFE_WRITE"


def test_refactor_task():
    plan = TaskPlanner().plan(
        "refactor the authentication module"
    )

    assert plan is not None
    assert plan.action == "refactor"
    assert plan.target == "the authentication module"
    assert plan.permission == "SAFE_WRITE"


def test_unrelated_message_is_not_task():
    assert TaskPlanner().plan("hello Genos") is None


def test_runtime_uses_task_planner_for_explicit_file_content(tmp_path):
    from app.chat import GenosRuntime

    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "Create a file called settings.txt containing hello world"
    )

    assert "Plan:" in response
    assert "settings.txt" in response
    assert "SAFE_WRITE" in response
    assert runtime.workflow.pending is not None
