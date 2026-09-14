from pathlib import Path

from app.chat.runtime import GenosRuntime
from app.memory import MemoryManager, MemoryRepository
from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools
from app.verification import VerificationEngine
from app.agent.workflow import AgentWorkflow


def workflow_for(tmp_path: Path):
    permissions = PermissionManager()
    actions = ProjectActionTools(tmp_path, permissions)
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )
    verifier = VerificationEngine(
        tmp_path,
        actions,
    )

    return AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        verifier,
        memory,
        "workspace-test",
    )


def test_workflow_requests_permission(tmp_path: Path):
    workflow = workflow_for(tmp_path)

    response = workflow.plan_write(
        "hello.txt",
        "hello",
    )

    assert "SAFE_WRITE" in response
    assert workflow.pending is not None
    assert not (tmp_path / "hello.txt").exists()


def test_workflow_approve_without_permission_is_blocked(tmp_path: Path):
    workflow = workflow_for(tmp_path)

    workflow.plan_write("hello.txt", "hello")
    response = workflow.approve()

    assert "Permission denied: SAFE_WRITE" in response
    assert not (tmp_path / "hello.txt").exists()


def test_workflow_write_verify_remember(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    actions = ProjectActionTools(tmp_path, permissions)
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )
    verifier = VerificationEngine(tmp_path, actions)

    workflow = AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        verifier,
        memory,
        "workspace-test",
    )

    workflow.plan_write("hello.txt", "hello")
    response = workflow.approve()

    assert "ACT: SUCCESS" in response
    assert "VERIFY: PASSED" in response
    assert "REMEMBER: Saved" in response
    assert (tmp_path / "hello.txt").read_text(
        encoding="utf-8"
    ) == "hello"


def test_workflow_deny_cancels(tmp_path: Path):
    workflow = workflow_for(tmp_path)

    workflow.plan_write("hello.txt", "hello")
    response = workflow.deny()

    assert "Cancelled write" in response
    assert workflow.pending is None
    assert not (tmp_path / "hello.txt").exists()


def test_runtime_workflow_requests_permission(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "plan write file hello.txt :: hello"
    )

    assert "SAFE_WRITE" in response

    blocked = runtime.handle("approve")
    assert "Permission denied: SAFE_WRITE" in blocked


def test_runtime_workflow_write(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("grant safe write")
    runtime.handle(
        "plan write file hello.txt :: hello"
    )

    response = runtime.handle("approve")

    assert "ACT: SUCCESS" in response
    assert "VERIFY: PASSED" in response
    assert (tmp_path / "hello.txt").read_text(
        encoding="utf-8"
    ) == "hello"
