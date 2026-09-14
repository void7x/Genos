from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.memory import MemoryManager
from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools
from app.verification import VerificationEngine


@dataclass(frozen=True)
class WorkflowPlan:
    action: str
    target: str
    details: str = ""


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

        self.pending = PendingAction(
            PermissionLevel.SAFE_WRITE,
            WorkflowPlan(
                action="write",
                target=target,
                details=content,
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

    def plan_execute(self, command: str) -> str:
        command = command.strip()

        if not command:
            return "Command cannot be empty."

        self.pending = PendingAction(
            PermissionLevel.EXECUTE,
            WorkflowPlan(
                action="execute",
                target=command,
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

        if pending.plan.action == "write":
            return self._perform_write(pending.plan)

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
            return "\n".join(
                [
                    "ACT: SUCCESS",
                    result.output,
                    "",
                    "VERIFY: FAILED",
                    verification.summary,
                ]
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

    def _perform_execute(self, plan: WorkflowPlan) -> str:
        result = self.action_tools.execute_command(plan.target)

        if not result.success:
            return "\n".join(
                [
                    "ACT: FAILED",
                    result.error or result.output,
                ]
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

