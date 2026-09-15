from pathlib import Path

from app.agent.workflow import AgentWorkflow
from app.memory import MemoryManager, MemoryRepository
from app.permissions import (
    PermissionLevel,
    PermissionManager,
)
from app.tasks import TaskManager, TaskRepository
from app.tools import ProjectActionTools
from app.verification import VerificationEngine


def build_workflow(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)
    permissions.grant(PermissionLevel.EXECUTE)

    tools = ProjectActionTools(
        tmp_path,
        permissions,
    )
    verifier = VerificationEngine(
        tmp_path,
        tools,
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
        tools,
        verifier,
        memory,
        "workspace-a",
        task_manager=tasks,
    )

    return workflow, tasks


def test_successful_workflow_completes_current_task(
    tmp_path,
):
    workflow, tasks = build_workflow(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Create notes",
        "Improve project",
    )

    response = workflow.plan_write(
        "notes.txt",
        "hello",
    )

    assert "approve" in response.casefold()

    result = workflow.approve()
    saved = tasks.get(
        "workspace-a",
        task.id,
    )

    assert "VERIFY: PASSED" in result
    assert saved is not None
    assert saved.status == "completed"


def test_failed_workflow_marks_current_task_failed(
    tmp_path,
):
    workflow, tasks = build_workflow(tmp_path)

    task = tasks.add(
        "workspace-a",
        "Run blocked command",
        "Improve project",
    )

    workflow.plan_execute("python -c fail")
    result = workflow.approve()

    saved = tasks.get(
        "workspace-a",
        task.id,
    )

    assert "ACT: FAILED" in result
    assert saved is not None
    assert saved.status == "failed"
