from __future__ import annotations

from pathlib import Path

from app.chat.intent import IntentRouter
from app.chat.context import ConversationContext
from app.agent import AgentOrchestrator, AgentWorkflow
from app.agent.task_planner import TaskPlanner
from app.agent.coding_executor import CodingTaskExecutor
from app.conversation.repository import ConversationRepository
from app.goals.models import Goal
from app.goals.repository import GoalRepository
from app.memory import MemoryManager, MemoryRepository
from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools, ProjectTools
from app.verification import VerificationEngine
from app.workspace import (
    ProjectInspector,
    WorkspaceManager,
    WorkspaceRepository,
)


class GenosRuntime:
    """Local deterministic chat runtime for Genos v1."""

    def __init__(
        self,
        workspace_path: str | Path,
        data_root: str | Path | None = None,
    ):
        self.root = Path(workspace_path).expanduser().resolve(strict=True)

        if not self.root.is_dir():
            raise ValueError(f"Workspace is not a directory: {self.root}")

        data = (
            Path(data_root).expanduser().resolve()
            if data_root is not None
            else self.root / "data"
        )

        self.data_root = data

        self.workspace_manager = WorkspaceManager(
            WorkspaceRepository(data / "workspaces.json")
        )
        self.workspace = self.workspace_manager.attach(self.root)

        self.inspector = ProjectInspector()
        self.tools = ProjectTools(self.root)
        self.permissions = PermissionManager()
        self.action_tools = ProjectActionTools(self.root, self.permissions)
        self.intent_router = IntentRouter()
        self.task_planner = TaskPlanner()
        self.coding_executor = CodingTaskExecutor(self.root)
        self.orchestrator = AgentOrchestrator(self.root)
        self.verifier = VerificationEngine(self.root, self.action_tools)
        self.verifier = VerificationEngine(self.root, self.action_tools)

        self.memory = MemoryManager(
            MemoryRepository(data / "memory")
        )

        self.workflow = AgentWorkflow(
            self.root,
            self.permissions,
            self.action_tools,
            self.verifier,
            self.memory,
            self.workspace.id,
        )

        self.goals = GoalRepository(data / "goals.json")

        self.conversation = ConversationRepository(
            data / "conversation" / f"{self.workspace.id}.json"
        )
        self.context = ConversationContext(self.conversation)

    def _activate_workspace(self, workspace) -> None:
        self.workspace = workspace
        self.root = Path(workspace.path).resolve(strict=True)
        self.tools = ProjectTools(self.root)
        self.orchestrator = AgentOrchestrator(self.root)
        self.verifier = VerificationEngine(self.root, self.action_tools)
        self.verifier = VerificationEngine(self.root, self.action_tools)
        self.conversation = ConversationRepository(
            self.data_root / "conversation" / f"{workspace.id}.json"
        )
        self.context = ConversationContext(self.conversation)

    def _workspace_list(self) -> str:
        workspaces = self.workspace_manager.list()

        if not workspaces:
            return "No workspaces are registered."

        lines = ["Registered workspaces:"]
        for workspace in workspaces:
            marker = "*" if workspace.id == self.workspace.id else " "
            lines.append(f"{marker} {workspace.name} [{workspace.id}]")
            lines.append(f"    {workspace.path}")

        return "\n".join(lines)

    def _switch_workspace(self, target: str) -> str:
        target = target.strip()

        if not target:
            return "Please specify a workspace name."

        workspaces = self.workspace_manager.list()

        match = next(
            (
                workspace
                for workspace in workspaces
                if workspace.name.casefold() == target.casefold()
                or workspace.id.casefold() == target.casefold()
                or workspace.path.casefold() == target.casefold()
            ),
            None,
        )

        if match is None:
            return f"Workspace not found: {target}"

        try:
            workspace = self.workspace_manager.switch(match.id)
            self._activate_workspace(workspace)
        except (ValueError, OSError) as exc:
            return f"Could not switch workspace: {exc}"

        return (
            f"Switched workspace.\n"
            f"Active workspace: {self.workspace.name}\n"
            f"Path: {self.workspace.path}"
        )
    def handle(self, message: str) -> str:
        text = str(message).strip()
        normalized = text.casefold()
        if normalized in {
            "list workspaces",
            "list my workspaces",
            "show workspaces",
            "show my workspaces",
            "what projects do you know",
            "what projects do you have",
        }:
            response = self._workspace_list()
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        for prefix in (
            "switch to ",
            "go to ",
            "open ",
            "use ",
        ):
            if normalized.startswith(prefix):
                target = text[len(prefix):].strip()
                response = self._switch_workspace(target)
                return response
        for prefix in (
            "attach ",
            "attach project ",
            "add workspace ",
            "add project ",
        ):
            if normalized.startswith(prefix):
                target = text[len(prefix):].strip().strip('"')

                if not target:
                    response = "Please specify a workspace path."
                else:
                    try:
                        workspace = self.workspace_manager.attach(target)
                        self._activate_workspace(workspace)
                        response = (
                            f"Workspace attached and activated.\n"
                            f"Active workspace: {self.workspace.name}\n"
                            f"Path: {self.workspace.path}"
                        )
                    except (ValueError, OSError) as exc:
                        response = f"Could not attach workspace: {exc}"

                self.conversation.append_turn("user", text)
                self.conversation.append_turn("assistant", response)
                return response
        if normalized in {
            "grant safe write",
            "allow safe write",
            "enable safe write",
        }:
            self.permissions.grant(PermissionLevel.SAFE_WRITE)
            response = "SAFE_WRITE permission granted."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "grant destructive",
            "allow destructive",
            "enable destructive",
        }:
            self.permissions.grant(PermissionLevel.DESTRUCTIVE)
            response = "DESTRUCTIVE permission granted."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "revoke destructive",
            "disable destructive",
        }:
            self.permissions.revoke(PermissionLevel.DESTRUCTIVE)
            response = "DESTRUCTIVE permission revoked."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "grant execute",
            "allow execute",
            "enable execute",
        }:
            self.permissions.grant(PermissionLevel.EXECUTE)
            response = "EXECUTE permission granted."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "revoke safe write",
            "disable safe write",
        }:
            self.permissions.revoke(PermissionLevel.SAFE_WRITE)
            response = "SAFE_WRITE permission revoked."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "revoke execute",
            "disable execute",
        }:
            self.permissions.revoke(PermissionLevel.EXECUTE)
            response = "EXECUTE permission revoked."
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        write_prefixes = (
            "write file ",
            "create file ",
            "overwrite file ",
        )

        for prefix in write_prefixes:
            if normalized.startswith(prefix):
                payload = text[len(prefix):].strip()

                if " :: " not in payload:
                    response = (
                        "Write format: write file <path> :: <content>"
                    )
                else:
                    relative_path, content = payload.split(
                        " :: ",
                        1,
                    )
                    overwrite = normalized.startswith("overwrite file ")

                    result = self.action_tools.write_file(
                        relative_path.strip(),
                        content,
                        overwrite=overwrite,
                    )
                    response = (
                        result.output
                        if result.success
                        else result.error
                    )

                self.conversation.append_turn("user", text)
                self.conversation.append_turn("assistant", response)
                return response

        for prefix in (
            "delete file ",
            "remove file ",
        ):
            if normalized.startswith(prefix):
                relative_path = text[len(prefix):].strip()
                result = self.action_tools.delete_file(relative_path)
                response = (
                    result.output
                    if result.success
                    else result.error
                )

                self.conversation.append_turn("user", text)
                self.conversation.append_turn("assistant", response)
                return response

        for prefix in (
            "execute ",
            "run command ",
        ):
            if normalized.startswith(prefix):
                command = text[len(prefix):].strip()

                if command.casefold() == "tests":
                    command = "python -m pytest -q"

                result = self.action_tools.execute_command(command)
                response = (
                    result.output
                    if result.success
                    else result.error
                )

                if result.success and not response:
                    response = "Command completed successfully."

                self.conversation.append_turn("user", text)
                self.conversation.append_turn("assistant", response)
                return response

        if normalized in {
            "run tests",
            "run the tests",
            "execute tests",
        }:
            result = self.action_tools.execute_command(
                "python -m pytest -q"
            )
            response = (
                result.output
                if result.success
                else result.error
            )

            if result.success and not response:
                response = "Tests completed successfully."

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "verify project",
            "verify this project",
            "check my project",
        }:
            result = self.verifier.verify_project()
            response = self._verification_response(result)
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "verify git",
            "verify git status",
            "verify repository",
        }:
            result = self.verifier.verify_git()
            response = self._verification_response(result)
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized in {
            "verify tests",
            "verify test suite",
            "verify the tests",
        }:
            result = self.verifier.verify_tests()
            response = self._verification_response(result)
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized.startswith("verify file "):
            relative_path = text[len("verify file "):].strip()
            result = self.verifier.verify_file(relative_path)
            response = self._verification_response(result)
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response


        if normalized == "approve":
            response = self.workflow.approve()
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized == "deny":
            response = self.workflow.deny()
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized.startswith("plan write file "):
            payload = text[len("plan write file "):].strip()

            if " :: " not in payload:
                response = (
                    "Workflow write format: "
                    "plan write file <path> :: <content>"
                )
            else:
                relative_path, content = payload.split(" :: ", 1)
                response = self.workflow.plan_write(
                    relative_path.strip(),
                    content,
                )

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if normalized.startswith("plan execute "):
            command = text[len("plan execute "):].strip()
            response = self.workflow.plan_execute(command)
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if (
            normalized.startswith("create a notes file")
            or normalized.startswith("create notes file")
            or normalized.startswith("make a notes file")
            or normalized.startswith("make notes file")
        ):
            status = self._project_info()

            content = (
                "# Project Status\n\n"
                + status
                + "\n"
            )

            response = self.workflow.plan_write(
                "notes/project_status.md",
                content,
            )

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        intent = self.intent_router.route(text)

        task_plan = self.task_planner.plan(text)

        if task_plan is not None:
            lines = [
                "Plan:",
                f"Task: {task_plan.action.replace('_', ' ').title()}",
            ]

            if task_plan.target:
                lines.append(f"Target: {task_plan.target}")

            if task_plan.details:
                lines.append(f"Details: {task_plan.details}")

            if task_plan.permission:
                lines.extend(
                    [
                        "",
                        f"Permission required: {task_plan.permission}",
                    ]
                )

            lines.extend(
                [
                    "",
                    "Steps:",
                    *[
                        f"{index}. {step}"
                        for index, step in enumerate(task_plan.steps, 1)
                    ],
                ]
            )

            if (
                task_plan.action == "create_file"
                and task_plan.target
                and task_plan.details
            ):
                response = self.workflow.plan_write(
                    task_plan.target,
                    task_plan.details,
                )

            elif task_plan.action == "add_logging":
                prepared = self.coding_executor.prepare(
                    task_plan.action,
                    task_plan.target,
                    task_plan.details,
                )

                if prepared is None:
                    response = (
                        "\n".join(lines)
                        + "\n\n"
                        "I could not safely prepare this coding change."
                    )
                else:
                    target, new_content = prepared
                    response = self.workflow.plan_edit(
                        target,
                        new_content,
                        reason=(
                            "Prepare a focused logging change "
                            "to the target Python module"
                        ),
                    )

            else:
                response = "\n".join(lines)

                if task_plan.action == "create_file":
                    response += (
                        "\n\n"
                        "I need the intended file content "
                        "before I can create it."
                    )

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if intent.name == "context_file":
            relative_path = self.context.last_file()

            if not relative_path:
                response = (
                    "I do not have a recent file reference to use yet."
                )
            else:
                result = self.tools.read_file(relative_path)
                response = (
                    result.output
                    if result.success
                    else result.error
                )

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        if intent.name == "context_followup":
            previous = self.context.previous_response()

            if previous:
                response = (
                    "Based on the previous step:\n"
                    + previous
                )
            else:
                response = "There is no previous result to refer to yet."

            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response

        semantic_responses = {
            "approve": lambda: self.workflow.approve(),
            "deny": lambda: self.workflow.deny(),
            "grant_safe_write": lambda: self._grant_permission(
                PermissionLevel.SAFE_WRITE
            ),
            "grant_execute": lambda: self._grant_permission(
                PermissionLevel.EXECUTE
            ),
            "grant_destructive": lambda: self._grant_permission(
                PermissionLevel.DESTRUCTIVE
            ),
            "revoke_safe_write": lambda: self._revoke_permission(
                PermissionLevel.SAFE_WRITE
            ),
            "revoke_execute": lambda: self._revoke_permission(
                PermissionLevel.EXECUTE
            ),
            "revoke_destructive": lambda: self._revoke_permission(
                PermissionLevel.DESTRUCTIVE
            ),
            "workspace_list": self._workspace_list,
            "workspace_switch": lambda: self._switch_workspace(
                intent.argument
            ),
            "delete_file": lambda: self._delete_file_natural(
                intent.argument
            ),
            "run_tests": lambda: self._run_tests_natural(),
            "verify_project": lambda: self._verification_response(
                self.verifier.verify_project()
            ),
            "verify_git": lambda: self._verification_response(
                self.verifier.verify_git()
            ),
            "verify_tests": lambda: self._verification_response(
                self.verifier.verify_tests()
            ),
            "verify_file": lambda: self._verification_response(
                self.verifier.verify_file(intent.argument)
            ),
            "natural_project_status": lambda: self.workflow.plan_write(
                "notes/project_status.md",
                "# Project Status\n\n" + self._project_info() + "\n",
            ),
        }

        if intent.name == "workspace_switch":
            return self._switch_workspace(intent.argument)

        if intent.name in semantic_responses:
            response = semantic_responses[intent.name]()
            self.conversation.append_turn("user", text)
            self.conversation.append_turn("assistant", response)
            return response


        if intent.name == "empty":
            response = (
                "Please enter a command. Type 'help' to see what I understand."
            )

        elif intent.name == "help":
            response = self._help()

        elif intent.name == "exit":
            response = "Goodbye."

        elif intent.name == "hello":
            response = (
                f"Hello. I'm Genos.\n"
                f"Active workspace: {self.workspace.name}"
            )

        elif intent.name == "capabilities":
            response = self._capabilities()

        elif intent.name == "project_info":
            response = self._project_info()

        elif (
            intent.name in {"find", "unknown"}
            and any(
                marker in normalized
                for marker in (
                    "explain",
                    "inspect",
                    "understand",
                    "show me how",
                    "show how",
                    "analyze",
                    "analyse",
                    "diagnose",
                )
            )
        ):
            orchestrated = self.orchestrator.run(text)

            response = (
                orchestrated
                if orchestrated is not None
                else (
                    "I could not build a plan for that request yet."
                )
            )

        elif intent.name == "list_files":
            result = self.tools.list_files(
                intent.argument or "."
            )
            response = result.output if result.success else result.error

        elif intent.name == "read_file":
            relative_path = self.context.resolve_file_reference(
                intent.argument
            )

            if not relative_path:
                relative_path = self.context.resolve_main_file()

            result = self.tools.read_file(relative_path)

            response = (
                result.output
                if result.success
                else result.error
            )

        elif intent.name == "find":
            result = self.tools.search_files(intent.argument)
            response = result.output or "(no matches)"

        elif intent.name == "git_status":
            response = self._git_status()

        elif intent.name == "git_log":
            result = self.tools.git_log(10)
            response = (
                result.output
                if result.success
                else result.error
            )

        elif intent.name == "goals":
            response = self._goals()

        elif intent.name == "memory":
            response = self._memory(intent.argument)

        elif intent.name == "remember":
            response = self._remember(intent.argument)

        elif intent.name == "goal":
            response = self._add_goal(intent.argument)

        elif intent.name == "permissions":
            response = self._permissions()

        else:
            response = (
                "I don't understand that yet.\n"
                "Try asking about the project, files, Git, goals, "
                "memory, permissions, or my features."
            )

        if intent.name != "exit":
            self.conversation.append_turn(text, response)

        return response

    def run(self) -> None:
        info = self.inspector.inspect(self.root)

        print()
        print("========================")
        print("         GENOS")
        print("========================")
        print(f"Workspace: {info.name}")
        print(f"Type:      {info.project_type}")
        print(
            f"Language:  "
            f"{', '.join(info.languages) or 'Unknown'}"
        )
        print(f"Git:       {info.git_branch or 'Not available'}")
        print(
            f"Status:    "
            f"{'Clean' if info.git_clean else 'Changes present'}"
        )
        print()
        print("Type 'help' for commands or 'exit' to quit.")
        print()

        while True:
            try:
                message = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                print("Goodbye.")
                break

            if not message:
                continue

            response = self.handle(message)

            print()
            print(f"Genos > {response}")
            print()

            if self.intent_router.route(message).name == "exit":
                break

    @staticmethod
    def _verification_response(result) -> str:
        lines = [
            "VERIFICATION: "
            + ("PASSED" if result.success else "FAILED"),
            result.summary,
        ]

        if result.checks:
            lines.append("")
            lines.append("Checks:")
            lines.extend(
                f"- {check}"
                for check in result.checks
            )

        return "\n".join(lines)


    def _grant_permission(self, permission: PermissionLevel) -> str:
        self.permissions.grant(permission)
        return f"{permission.name} permission granted."

    def _revoke_permission(self, permission: PermissionLevel) -> str:
        self.permissions.revoke(permission)
        return f"{permission.name} permission revoked."

    def _delete_file_natural(self, relative_path: str) -> str:
        result = self.action_tools.delete_file(relative_path)
        return result.output if result.success else result.error

    def _run_tests_natural(self) -> str:
        result = self.action_tools.execute_command(
            "python -m pytest -q"
        )
        return result.output if result.success else result.error

    def _capabilities(self) -> str:
        return "\n".join(
            [
                "I can currently:",
                "",
                "- Understand the active project",
                "- Detect project language and structure",
                "- List and read project files",
                "- Search project files",
                "- Inspect Git status and commit history",
                "- Store and search project memory",
                "- Track workspace-specific goals",
                "- Check my current permissions",
                "- Keep a local conversation history",
            ]
        )

    def _project_info(self) -> str:
        info = self.inspector.inspect(self.root)

        return "\n".join(
            [
                f"Name: {info.name}",
                f"Type: {info.project_type}",
                f"Languages: {', '.join(info.languages) or 'Unknown'}",
                f"Frameworks: {', '.join(info.frameworks) or 'None detected'}",
                f"Source directories: {', '.join(info.source_dirs) or 'None'}",
                f"Test directories: {', '.join(info.test_dirs) or 'None'}",
                f"README: {info.readme or 'None'}",
                f"Git repository: {'yes' if info.is_git_repo else 'no'}",
                f"Git branch: {info.git_branch or 'Unknown'}",
                f"Git clean: {info.git_clean}",
                f"Test commands: {', '.join(info.test_commands) or 'None detected'}",
            ]
        )

    def _git_status(self) -> str:
        result = self.tools.git_status()

        if not result.success:
            return result.error

        return result.output or "Working tree clean."

    def _goals(self) -> str:
        goals = self.goals.list(self.workspace.id)

        if not goals:
            return "No goals for this workspace."

        return "\n".join(
            f"- [{goal.status}] {goal.title} ({goal.priority})"
            for goal in goals
        )

    def _memory(self, query: str) -> str:
        if not query:
            return "Memory query cannot be empty."

        memories = self.memory.search(
            self.workspace.id,
            query,
        )

        if not memories:
            return "No matching memories."

        return "\n".join(
            f"- {memory.content}"
            for memory in memories
        )

    def _remember(self, content: str) -> str:
        if not content:
            return "Memory content cannot be empty."

        memory = self.memory.add(
            self.workspace.id,
            content,
            ("chat",),
        )

        return f"Remembered: {memory.content}"

    def _add_goal(self, title: str) -> str:
        if not title:
            return "Goal title cannot be empty."

        goal = self.goals.add(
            Goal(
                title=title,
                workspace_id=self.workspace.id,
            ),
            self.workspace.id,
        )

        return f"Goal: {goal.title}"

    def _permissions(self) -> str:
        return "\n".join(
            [
                "READ: "
                + str(
                    self.permissions.is_allowed(
                        PermissionLevel.READ
                    )
                ),
                "SAFE_WRITE: "
                + str(
                    self.permissions.is_allowed(
                        PermissionLevel.SAFE_WRITE
                    )
                ),
                "EXECUTE: "
                + str(
                    self.permissions.is_allowed(
                        PermissionLevel.EXECUTE
                    )
                ),
                "DESTRUCTIVE: "
                + str(
                    self.permissions.is_allowed(
                        PermissionLevel.DESTRUCTIVE
                    )
                ),
            ]
        )

    @staticmethod
    def _help() -> str:
        return "\n".join(
            [
                "You can ask me naturally about:",
                "",
                "  the project",
                "  files",
                "  a specific file",
                "  searching the project",
                "  Git status and history",
                "  goals",
                "  memory",
                "  permissions",
                "  my features",
                "",
                "Examples:",
                "  what features do you have?",
                "  tell me about this project",
                "  show me the project files",
                "  search for PermissionManager",
                "  are there any uncommitted changes?",
                "  what are my goals?",
                "  what can you modify?",
            ]
        )


def main() -> None:
    GenosRuntime(Path.cwd()).run()














