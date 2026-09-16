from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.agent.workflow import AgentWorkflow
from app.tasks import TaskManager


@dataclass(frozen=True)
class MultiStep:
    action: str
    target: str
    details: str = ""
    reason: str = ""


@dataclass(frozen=True)
class MultiStepPlan:
    task_id: str
    title: str
    steps: tuple[MultiStep, ...]


class MultiStepWorkflow:
    """Execute a reviewable sequence as one task."""

    def __init__(
        self,
        root: str | Path,
        workflow: AgentWorkflow,
        tasks: TaskManager,
    ):
        self.root = (
            Path(root)
            .expanduser()
            .resolve(strict=True)
        )
        self.workflow = workflow
        self.tasks = tasks
        self.pending: MultiStepPlan | None = None

    def plan_add_logging(
        self,
        task_id: str,
        target: str,
        new_content: str,
    ) -> MultiStepPlan:
        plan = MultiStepPlan(
            task_id=task_id,
            title=f"Add logging to {target}",
            steps=(
                MultiStep(
                    action="edit",
                    target=target,
                    details=new_content,
                    reason="Apply focused logging change",
                ),
                MultiStep(
                    action="execute",
                    target="python -m pytest -q",
                    reason="Run the full test suite",
                ),
            ),
        )

        self.pending = plan
        return plan

    def approve(
        self,
        workspace_id: str,
    ) -> str:
        if self.pending is None:
            return "There is no pending multi-step workflow."

        plan = self.pending
        self.pending = None

        started = self.tasks.start(
            workspace_id,
            plan.task_id,
        )

        if started is None:
            return f"Task not found: {plan.task_id}"

        lines = [
            "MULTI-STEP WORKFLOW",
            f"Task: {started.title}",
            "",
        ]

        for index, step in enumerate(
            plan.steps,
            1,
        ):
            lines.append(
                f"{index}. {step.reason or step.action}"
            )

        lines.append("")

        # Use an inner workflow without task binding.
        step_workflow = AgentWorkflow(
            self.root,
            self.workflow.permissions,
            self.workflow.action_tools,
            self.workflow.verifier,
            self.workflow.memory,
            workspace_id,
            self.workflow.history,
            None,
        )

        for index, step in enumerate(
            plan.steps,
            1,
        ):
            lines.append(
                f"STEP {index}: {step.action.upper()}"
            )

            if step.action == "edit":
                planning = step_workflow.plan_edit(
                    step.target,
                    step.details,
                    reason=step.reason or "Update file",
                )

            elif step.action == "execute":
                planning = step_workflow.plan_execute(
                    step.target,
                )

            else:
                self.tasks.fail(
                    workspace_id,
                    plan.task_id,
                )
                return "\n".join(
                    [
                        *lines,
                        f"WORKFLOW: FAILED",
                        f"Unsupported step: {step.action}",
                        "TASK: failed",
                    ]
                )

            permission = step_workflow.pending

            if permission is not None:
                if not self.workflow.permissions.is_allowed(
                    permission.permission
                ):
                    self.tasks.fail(
                        workspace_id,
                        plan.task_id,
                    )

                    return "\n".join(
                        [
                            *lines,
                            planning,
                            "",
                            (
                                "WORKFLOW: FAILED"
                            ),
                            (
                                "Permission required: "
                                f"{permission.permission.name}"
                            ),
                            "TASK: failed",
                        ]
                    )

                result = step_workflow.approve()

            else:
                result = planning

            lines.extend(
                [
                    result,
                    "",
                ]
            )

            if (
                "ACT: FAILED" in result
                or "VERIFY: FAILED" in result
                or "ROLLBACK: FAILED" in result
            ):
                self.tasks.fail(
                    workspace_id,
                    plan.task_id,
                )

                lines.extend(
                    [
                        "WORKFLOW: FAILED",
                        "Execution stopped after the failed step.",
                        "TASK: failed",
                    ]
                )

                return "\n".join(lines)

        self.tasks.complete(
            workspace_id,
            plan.task_id,
        )

        lines.extend(
            [
                "WORKFLOW: COMPLETED",
                "All steps completed successfully.",
                "TASK: completed",
            ]
        )

        return "\n".join(lines)
