from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.agent.action_history import ActionHistoryManager
from app.agent.rollback import RollbackManager
from app.memory import MemoryManager
from app.permissions import PermissionLevel, PermissionManager
from app.tasks import TaskManager
from app.tools import ProjectActionTools
from app.verification import VerificationEngine


@dataclass(frozen=True)
class WorkflowPlan:
    action: str
    target: str
    details: str = ""
    original_content: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class PendingAction:
    permission: PermissionLevel
    plan: WorkflowPlan


class AgentWorkflow:
    """Coordinate plan -> permission -> action -> verify -> remember."""

    def __init__(
        self,
        workspace_path: str | Path,
        permissions: PermissionManager,
        action_tools: ProjectActionTools,
        verifier: VerificationEngine,
        memory: MemoryManager,
        workspace_id: str,
        history: ActionHistoryManager | None = None,
        task_manager: TaskManager | None = None,
    ):
        self.root = (
            Path(workspace_path)
            .expanduser()
            .resolve(strict=True)
        )

        if not self.root.is_dir():
            raise ValueError(
                f"Workspace is not a directory: {self.root}"
            )

        self.permissions = permissions
        self.action_tools = action_tools
        self.verifier = verifier
        self.memory = memory
        self.workspace_id = workspace_id
        self.history = history
        self.task_manager = task_manager
        self.pending: PendingAction | None = None

    def plan_write(
        self,
        relative_path: str,
        content: str,
    ) -> str:
        target = relative_path.strip()

        if not target:
            return "Write target cannot be empty."

        target_path = (self.root / target).resolve()

        try:
            target_path.relative_to(self.root)
        except ValueError:
            return "Write target escapes the active workspace."

        if target_path.exists():
            return (
                f"Target already exists: {target}\n"
                "I will not overwrite an existing file automatically.\n"
                "Use the explicit 'overwrite file' command when you intend to replace it."
            )

        current_task = (
            self.task_manager.current(self.workspace_id)
            if self.task_manager is not None
            else None
        )

        self.pending = PendingAction(
            PermissionLevel.SAFE_WRITE,
            WorkflowPlan(
                action="write",
                target=target,
                details=content,
                task_id=(
                    current_task.id
                    if current_task is not None
                    else ""
                ),
            ),
        )

        lines = [
            "Plan:",
            f"1. Create {target}",
            "2. Verify the file and expected content",
            "3. Remember the completed action",
            "",
            "Permission required: SAFE_WRITE",
            "Type 'approve' to continue or 'deny' to cancel.",
        ]

        return "\n".join(lines)

    def plan_edit(
        self,
        relative_path: str,
        new_content: str,
        *,
        reason: str = "Update the file",
    ) -> str:
        target = relative_path.strip()

        if not target:
            return "Edit target cannot be empty."

        target_path = (self.root / target).resolve()

        try:
            target_path.relative_to(self.root)
        except ValueError:
            return "Edit target escapes the active workspace."

        if not target_path.exists():
            return f"File not found: {target}"

        if not target_path.is_file():
            return f"Not a file: {target}"

        try:
            original = target_path.read_text(encoding="utf-8")
        except OSError as exc:
            return f"Could not read {target}: {exc}"

        if original == new_content:
            return f"No changes required: {target}"

        current_task = (
            self.task_manager.current(self.workspace_id)
            if self.task_manager is not None
            else None
        )

        self.pending = PendingAction(
            PermissionLevel.SAFE_WRITE,
            WorkflowPlan(
                action="edit",
                target=target,
                details=new_content,
                original_content=original,
                task_id=(
                    current_task.id
                    if current_task is not None
                    else ""
                ),
            ),
        )

        return "\n".join(
            [
                "Plan:",
                f"1. {reason}",
                f"2. Update {target}",
                "3. Verify the resulting file content",
                "4. Remember the completed action",
                "",
                "Permission required: SAFE_WRITE",
                "Type 'approve' to continue or 'deny' to cancel.",
            ]
        )

    def plan_execute(self, command: str) -> str:
        command = command.strip()

        if not command:
            return "Command cannot be empty."

        current_task = (
            self.task_manager.current(self.workspace_id)
            if self.task_manager is not None
            else None
        )

        self.pending = PendingAction(
            PermissionLevel.EXECUTE,
            WorkflowPlan(
                action="execute",
                target=command,
                task_id=(
                    current_task.id
                    if current_task is not None
                    else ""
                ),
            ),
        )

        lines = [
            "Plan:",
            f"1. Execute: {command}",
            "2. Verify the command result",
            "3. Remember the completed action",
            "",
            "Permission required: EXECUTE",
            "Type 'approve' to continue or 'deny' to cancel.",
        ]

        return "\n".join(lines)

    def approve(self) -> str:
        if self.pending is None:
            return "There is no pending action."

        pending = self.pending

        if not self.permissions.is_allowed(pending.permission):
            return "\n".join(
                [
                    f"Permission denied: {pending.permission.name}",
                    "Grant it first, then type 'approve'.",
                ]
            )

        self.pending = None

        if (
            self.task_manager is not None
            and pending.plan.task_id
        ):
            self.task_manager.start(
                self.workspace_id,
                pending.plan.task_id,
            )

        if pending.plan.action == "write":
            return self._perform_write(pending.plan)

        if pending.plan.action == "edit":
            return self._perform_edit(pending.plan)

        if pending.plan.action == "execute":
            return self._perform_execute(pending.plan)

        return "Unknown pending action."

    def deny(self) -> str:
        if self.pending is None:
            return "There is no pending action."

        action = self.pending.plan.action
        target = self.pending.plan.target
        self.pending = None

        return f"Cancelled {action}: {target}"

    def _perform_write(self, plan: WorkflowPlan) -> str:
        result = self.action_tools.write_file(
            plan.target,
            plan.details,
            overwrite=False,
        )

        if not result.success:
            if (
                self.task_manager is not None
                and plan.task_id
            ):
                self.task_manager.fail(
                    self.workspace_id,
                    plan.task_id,
                )

            if self.history is not None:
                self.history.add(
                    self.workspace_id,
                    action="write",
                    target=plan.target,
                    status="failed",
                    summary=result.error,
                )

            return "\n".join(
                [
                    "ACT: FAILED",
                    result.error,
                ]
            )

        verification = self.verifier.verify_file(
            plan.target,
            expected_content=plan.details,
        )

        if not verification.success:
            if (
                self.task_manager is not None
                and plan.task_id
            ):
                self.task_manager.fail(
                    self.workspace_id,
                    plan.task_id,
                )

            if self.history is not None:
                self.history.add(
                    self.workspace_id,
                    action="write",
                    target=plan.target,
                    status="failed",
                    verification="failed",
                    summary=verification.summary,
                )

            return "\n".join(
                [
                    "ACT: SUCCESS",
                    result.output,
                    "",
                    "VERIFY: FAILED",
                    verification.summary,
                ]
            )

        if (
            self.task_manager is not None
            and plan.task_id
        ):
            self.task_manager.complete(
                self.workspace_id,
                plan.task_id,
            )

        if self.history is not None:
            self.history.add(
                self.workspace_id,
                action="write",
                target=plan.target,
                status="success",
                verification="passed",
                summary="Created file successfully.",
            )

        self.memory.add(
            self.workspace_id,
            f"Created {plan.target} through Genos workflow.",
            ("workflow", "write"),
        )

        return "\n".join(
            [
                "ACT: SUCCESS",
                result.output,
                "",
                "VERIFY: PASSED",
                verification.summary,
                "",
                "REMEMBER: Saved workflow completion to project memory.",
            ]
        )

    def _perform_edit(self, plan: WorkflowPlan) -> str:
        rollback = RollbackManager(self.root)
        snapshot = rollback.snapshot(
            plan.target,
            plan.original_content,
        )

        result = self.action_tools.write_file(
            plan.target,
            plan.details,
            overwrite=True,
        )

        if not result.success:
            if (
                self.task_manager is not None
                and plan.task_id
            ):
                self.task_manager.fail(
                    self.workspace_id,
                    plan.task_id,
                )

            if self.history is not None:
                self.history.add(
                    self.workspace_id,
                    action="edit",
                    target=plan.target,
                    status="failed",
                    summary=result.error,
                )

            return "\n".join(
                [
                    "ACT: FAILED",
                    result.error,
                ]
            )

        verification = self.verifier.verify_file(
            plan.target,
            expected_content=plan.details,
        )

        if not verification.success:
            rollback_result = rollback.restore(snapshot)

            if (
                self.task_manager is not None
                and plan.task_id
            ):
                self.task_manager.fail(
                    self.workspace_id,
                    plan.task_id,
                )

            if self.history is not None:
                self.history.add(
                    self.workspace_id,
                    action="edit",
                    target=plan.target,
                    status="failed",
                    verification="failed",
                    rollback=(
                        "passed"
                        if rollback_result.success
                        else "failed"
                    ),
                    summary=verification.summary,
                )

            return "\n".join(
                [
                    "ACT: SUCCESS",
                    result.output,
                    "",
                    "VERIFY: FAILED",
                    verification.summary,
                    "",
                    (
                        "ROLLBACK: PASSED"
                        if rollback_result.success
                        else "ROLLBACK: FAILED"
                    ),
                    rollback_result.summary,
                ]
            )

        if (
            self.task_manager is not None
            and plan.task_id
        ):
            self.task_manager.complete(
                self.workspace_id,
                plan.task_id,
            )

        if self.history is not None:
            self.history.add(
                self.workspace_id,
                action="edit",
                target=plan.target,
                status="success",
                verification="passed",
                summary="Edited file successfully.",
            )

        self.memory.add(
            self.workspace_id,
            f"Edited {plan.target} through Genos coding workflow.",
            ("workflow", "edit"),
        )

        return "\n".join(
            [
                "ACT: SUCCESS",
                result.output,
                "",
                "VERIFY: PASSED",
                verification.summary,
                "",
                "REMEMBER: Saved coding action to project memory.",
            ]
        )

    def _perform_execute(self, plan: WorkflowPlan) -> str:
        result = self.action_tools.execute_command(plan.target)

        if not result.success:
            if (
                self.task_manager is not None
                and plan.task_id
            ):
                self.task_manager.fail(
                    self.workspace_id,
                    plan.task_id,
                )

            if self.history is not None:
                self.history.add(
                    self.workspace_id,
                    action="execute",
                    target=plan.target,
                    status="failed",
                    summary=result.error or result.output,
                )

            return "\n".join(
                [
                    "ACT: FAILED",
                    result.error or result.output,
                ]
            )

        if (
            self.task_manager is not None
            and plan.task_id
        ):
            self.task_manager.complete(
                self.workspace_id,
                plan.task_id,
            )

        if self.history is not None:
            self.history.add(
                self.workspace_id,
                action="execute",
                target=plan.target,
                status="success",
                verification="passed",
                summary="Command returned success.",
            )

        self.memory.add(
            self.workspace_id,
            f"Executed '{plan.target}' through Genos workflow.",
            ("workflow", "execute"),
        )

        output = result.output or "(no output)"

        return "\n".join(
            [
                "ACT: SUCCESS",
                output,
                "",
                "VERIFY: PASSED",
                "Command returned success.",
                "",
                "REMEMBER: Saved workflow completion to project memory.",
            ]
        )
