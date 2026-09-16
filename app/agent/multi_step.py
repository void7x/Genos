from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.agent.workflow import AgentWorkflow
from app.tasks import TaskManager
from app.agent.workflow_state import WorkflowStateRepository


@dataclass(frozen=True)
class MultiStep:
    action: str
    target: str
    details: str = ""
    reason: str = ""
    depends_on: tuple[int, ...] = ()


@dataclass(frozen=True)
class MultiStepPlan:
    task_id: str
    title: str
    steps: tuple[MultiStep, ...]
    current_step: int = 1
    status: str = "pending"


class MultiStepWorkflow:
    """Execute a reviewable sequence as one task."""

    def __init__(
        self,
        root: str | Path,
        workflow: AgentWorkflow,
        tasks: TaskManager,
        state: WorkflowStateRepository,
    ):
        self.root = (
            Path(root)
            .expanduser()
            .resolve(strict=True)
        )
        self.workflow = workflow
        self.tasks = tasks
        self.state = state
        self.pending = self.state.load(
            workflow.workspace_id
        )

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
                    depends_on=(1,),
                ),
            ),
        )

        self.pending = plan
        self.state.save(
            self.workflow.workspace_id,
            plan,
        )
        return plan

    def resume(
        self,
        workspace_id: str,
    ) -> str:
        if self.pending is None:
            return "There is no interrupted multi-step workflow."

        if self.pending.status == "completed":
            return "The workflow is already completed."

        if self.pending.status == "failed":
            return "The workflow previously failed and cannot be resumed automatically."

        return self.approve(workspace_id)

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
            self.pending = plan
            return f"Task not found: {plan.task_id}"

        running_plan = MultiStepPlan(
            task_id=plan.task_id,
            title=plan.title,
            steps=plan.steps,
            current_step=max(1, plan.current_step),
            status="running",
        )
        self.pending = running_plan
        self.state.save(
            workspace_id,
            running_plan,
        )
        plan = running_plan

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

        start_index = max(1, plan.current_step)
        completed_steps = set(range(1, start_index))

        for index, step in enumerate(
            plan.steps,
            1,
        ):
            if index < start_index:
                continue

            missing_dependencies = tuple(
                dependency
                for dependency in step.depends_on
                if dependency not in completed_steps
            )

            if missing_dependencies:
                self.tasks.fail(
                    workspace_id,
                    plan.task_id,
                )

                failed_plan = MultiStepPlan(
                    task_id=plan.task_id,
                    title=plan.title,
                    steps=plan.steps,
                    current_step=index,
                    status="failed",
                )
                self.pending = failed_plan
                self.state.save(
                    workspace_id,
                    failed_plan,
                )

                return "\n".join(
                    [
                        *lines,
                        "WORKFLOW: FAILED",
                        (
                            f"STEP {index} blocked by dependencies: "
                            f"{missing_dependencies}"
                        ),
                        "TASK: failed",
                    ]
                )

            running_plan = MultiStepPlan(
                task_id=plan.task_id,
                title=plan.title,
                steps=plan.steps,
                current_step=index,
                status="running",
            )
            self.pending = running_plan
            self.state.save(
                workspace_id,
                running_plan,
            )
            plan = running_plan

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
                    self.state.save(
                        workspace_id,
                        plan,
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

                failed_plan = MultiStepPlan(
                    task_id=plan.task_id,
                    title=plan.title,
                    steps=plan.steps,
                    current_step=index,
                    status="failed",
                )
                self.pending = failed_plan
                self.state.save(
                    workspace_id,
                    failed_plan,
                )

                lines.extend(
                    [
                        "WORKFLOW: FAILED",
                        "Execution stopped after the failed step.",
                        "TASK: failed",
                    ]
                )

                return "\n".join(lines)

            completed_steps.add(index)

        self.tasks.complete(
            workspace_id,
            plan.task_id,
        )

        self.pending = None
        self.state.clear(workspace_id)

        lines.extend(
            [
                "WORKFLOW: COMPLETED",
                "All steps completed successfully.",
                "TASK: completed",
            ]
        )

        return "\n".join(lines)
