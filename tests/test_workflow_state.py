from app.agent.multi_step import MultiStep, MultiStepPlan
from app.agent.workflow_state import WorkflowStateRepository


def test_workflow_state_persists_and_reloads(tmp_path):
    repository = WorkflowStateRepository(
        tmp_path / "workflows"
    )

    plan = MultiStepPlan(
        task_id="task-123",
        title="Add logging",
        steps=(
            MultiStep(
                action="edit",
                target="sample.py",
                details="updated",
                reason="Apply logging",
            ),
            MultiStep(
                action="execute",
                target="python -m pytest -q",
                reason="Run tests",
            ),
        ),
    )

    repository.save("workspace-a", plan)

    assert repository.load("workspace-a") == plan

    repository.clear("workspace-a")

    assert repository.load("workspace-a") is None


def test_workflow_state_isolated_by_workspace(tmp_path):
    repository = WorkflowStateRepository(
        tmp_path / "workflows"
    )

    plan = MultiStepPlan(
        task_id="task-456",
        title="Workspace A workflow",
        steps=(
            MultiStep(
                action="edit",
                target="sample.py",
            ),
        ),
    )

    repository.save("workspace-a", plan)

    assert repository.load("workspace-a") == plan
    assert repository.load("workspace-b") is None


def test_workflow_state_preserves_resume_position(tmp_path):
    repository = WorkflowStateRepository(
        tmp_path / "workflows"
    )

    plan = MultiStepPlan(
        task_id="task-resume",
        title="Interrupted workflow",
        steps=(
            MultiStep(
                action="edit",
                target="sample.py",
            ),
            MultiStep(
                action="execute",
                target="python -m pytest -q",
            ),
        ),
        current_step=2,
        status="running",
    )

    repository.save("workspace-a", plan)

    loaded = repository.load("workspace-a")

    assert loaded is not None
    assert loaded.current_step == 2
    assert loaded.status == "running"
    assert loaded.steps[1].action == "execute"
