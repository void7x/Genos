from pathlib import Path

from app.agent.multi_step import (
    MultiStep,
    MultiStepPlan,
    MultiStepWorkflow,
)
from app.agent.workflow import AgentWorkflow
from app.agent.workflow_state import WorkflowStateRepository
from app.memory import MemoryManager, MemoryRepository
from app.permissions import PermissionLevel, PermissionManager
from app.tasks import TaskManager, TaskRepository
from app.tools import ProjectActionTools
from app.verification import VerificationEngine


def build_components(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)
    permissions.grant(PermissionLevel.EXECUTE)

    actions = ProjectActionTools(
        tmp_path,
        permissions,
    )
    verifier = VerificationEngine(
        tmp_path,
        actions,
    )
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )
    tasks = TaskManager(
        TaskRepository(tmp_path / "tasks")
    )

    workflow = AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        verifier,
        memory,
        "workspace-a",
    )

    state = WorkflowStateRepository(
        tmp_path / "workflows"
    )

    multi = MultiStepWorkflow(
        tmp_path,
        workflow,
        tasks,
        state,
    )

    return multi, tasks


def test_multistep_logging_workflow_completes_task(
    tmp_path,
):
    target = tmp_path / "sample.py"
    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_sample.py").write_text(
        "from sample import hello\n\n"
        "def test_hello():\n"
        "    assert hello() == 'hello'\n",
        encoding="utf-8",
    )

    multi, tasks = build_components(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Harden sample logging",
        "Improve reliability",
    )

    new_content = (
        "import logging\n"
        "logger = logging.getLogger(__name__)\n"
        "\n"
        "def hello():\n"
        '    logger.debug("Entering hello")\n'
        "    return 'hello'\n"
    )

    multi.plan_add_logging(
        task.id,
        "sample.py",
        new_content,
    )

    result = multi.approve("workspace-a")

    saved = tasks.get(
        "workspace-a",
        task.id,
    )

    assert "WORKFLOW: COMPLETED" in result
    assert saved is not None
    assert saved.status == "completed"
    assert "import logging" in target.read_text(
        encoding="utf-8"
    )


def test_multistep_stops_when_execution_fails(
    tmp_path,
):
    multi, tasks = build_components(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Run failure workflow",
        "Improve reliability",
    )

    multi.pending = MultiStepPlan(
        task_id=task.id,
        title="Failure workflow",
        steps=(
            MultiStep(
                action="execute",
                target="python -m pytest -q missing_suite.py",
                reason="Run failing test command",
            ),
        ),
    )

    result = multi.approve("workspace-a")

    saved = tasks.get(
        "workspace-a",
        task.id,
    )

    assert "WORKFLOW: FAILED" in result
    assert saved is not None
    assert saved.status == "failed"

def test_multistep_dependency_allows_dependent_step(tmp_path):
    multi, tasks = build_components(tmp_path)

    target = tmp_path / "sample.py"
    target.write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_sample.py").write_text(
        "from sample import hello\n\n"
        "def test_hello():\n"
        "    assert hello() == 'updated'\n",
        encoding="utf-8",
    )

    task = tasks.add(
        "workspace-a",
        "Dependency workflow",
        "Improve reliability",
    )

    multi.pending = MultiStepPlan(
        task_id=task.id,
        title="Dependency workflow",
        steps=(
            MultiStep(
                action="edit",
                target="sample.py",
                details="def hello():\n"
                "    return 'updated'\n",
                reason="Update implementation",
            ),
            MultiStep(
                action="execute",
                target="python -m pytest -q",
                reason="Run tests after edit",
                depends_on=(1,),
            ),
        ),
    )

    result = multi.approve("workspace-a")

    saved = tasks.get(
        "workspace-a",
        task.id,
    )

    assert "WORKFLOW: COMPLETED" in result
    assert saved is not None
    assert saved.status == "completed"

def test_multistep_blocks_unsatisfied_dependency(tmp_path):
    multi, tasks = build_components(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Blocked dependency workflow",
        "Improve reliability",
    )

    multi.pending = MultiStepPlan(
        task_id=task.id,
        title="Blocked dependency workflow",
        steps=(
            MultiStep(
                action="execute",
                target="python -m pytest -q",
                reason="Blocked step",
                depends_on=(2,),
            ),
        ),
    )

    result = multi.approve("workspace-a")

    saved = tasks.get("workspace-a", task.id)

    assert "blocked by dependencies" in result
    assert "WORKFLOW: FAILED" in result
    assert saved is not None
    assert saved.status == "failed"

def test_multistep_records_deterministic_failure_recovery(tmp_path):
    multi, tasks = build_components(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Recovery workflow",
        "Improve reliability",
    )

    multi.pending = MultiStepPlan(
        task_id=task.id,
        title="Recovery workflow",
        steps=(
            MultiStep(
                action="execute",
                target="python -m pytest -q missing_suite.py",
                reason="Run tests",
            ),
        ),
    )

    result = multi.approve("workspace-a")

    assert "RECOVERY: diagnose_failure" in result
    assert "WORKFLOW: FAILED" in result


def test_error_recovery_retries_transient_failure():
    from app.agent.error_recovery import ErrorRecoveryEngine
    from app.agent.test_failure_analyzer import TestFailureReport

    engine = ErrorRecoveryEngine()

    report = TestFailureReport(
        failed_tests=(),
        summary="Pytest reported a failure.",
    )

    decision = engine.decide(
        report,
        "Connection reset by peer",
    )

    assert decision.action == "retry_tests"
    assert decision.safe is True

