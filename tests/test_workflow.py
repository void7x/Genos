from pathlib import Path

from app.chat.runtime import GenosRuntime
from app.agent.action_history import ActionHistoryManager, ActionHistoryRepository
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

def test_workflow_rejects_existing_target(tmp_path: Path):
    target = tmp_path / "hello.txt"
    target.write_text("old", encoding="utf-8")

    workflow = workflow_for(tmp_path)

    response = workflow.plan_write(
        "hello.txt",
        "new",
    )

    assert "Target already exists" in response
    assert "will not overwrite" in response
    assert workflow.pending is None
    assert target.read_text(encoding="utf-8") == "old"

def test_workflow_edit_rolls_back_when_verification_fails(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    actions = ProjectActionTools(tmp_path, permissions)
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )

    class FailingVerifier:
        def verify_file(
            self,
            relative_path: str,
            expected_content: str | None = None,
        ):
            from app.verification.engine import VerificationResult

            return VerificationResult(
                False,
                f"Forced verification failure: {relative_path}",
            )

    workflow = AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        FailingVerifier(),
        memory,
        "workspace-test",
    )

    workflow.plan_edit(
        "config.py",
        "new = False\n",
    )

    response = workflow.approve()

    assert "ACT: SUCCESS" in response
    assert "VERIFY: FAILED" in response
    assert "ROLLBACK: PASSED" in response
    assert target.read_text(encoding="utf-8") == "old = True\n"


def test_workflow_records_successful_edit_in_history(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    actions = ProjectActionTools(tmp_path, permissions)
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )
    history = ActionHistoryManager(
        ActionHistoryRepository(tmp_path / "history")
    )
    verifier = VerificationEngine(tmp_path, actions)

    workflow = AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        verifier,
        memory,
        "workspace-test",
        history,
    )

    workflow.plan_edit(
        "config.py",
        "new = False\n",
    )

    response = workflow.approve()

    assert "VERIFY: PASSED" in response

    entries = history.list("workspace-test")

    assert len(entries) == 1
    assert entries[0].action == "edit"
    assert entries[0].target == "config.py"
    assert entries[0].status == "success"
    assert entries[0].verification == "passed"


def test_workflow_records_failed_edit_and_rollback_in_history(tmp_path: Path):
    permissions = PermissionManager()
    permissions.grant(PermissionLevel.SAFE_WRITE)

    target = tmp_path / "config.py"
    target.write_text("old = True\n", encoding="utf-8")

    actions = ProjectActionTools(tmp_path, permissions)
    memory = MemoryManager(
        MemoryRepository(tmp_path / "memory")
    )
    history = ActionHistoryManager(
        ActionHistoryRepository(tmp_path / "history")
    )

    class FailingVerifier:
        def verify_file(
            self,
            relative_path: str,
            expected_content: str | None = None,
        ):
            from app.verification.engine import VerificationResult

            return VerificationResult(
                False,
                f"Forced verification failure: {relative_path}",
            )

    workflow = AgentWorkflow(
        tmp_path,
        permissions,
        actions,
        FailingVerifier(),
        memory,
        "workspace-test",
        history,
    )

    workflow.plan_edit(
        "config.py",
        "new = False\n",
    )

    response = workflow.approve()

    assert "VERIFY: FAILED" in response
    assert "ROLLBACK: PASSED" in response

    entries = history.list("workspace-test")

    assert len(entries) == 1
    assert entries[0].action == "edit"
    assert entries[0].status == "failed"
    assert entries[0].verification == "failed"
    assert entries[0].rollback == "passed"
    assert target.read_text(encoding="utf-8") == "old = True\n"
