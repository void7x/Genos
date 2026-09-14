from __future__ import annotations

from pathlib import Path

from app.chat.intent import IntentRouter
from app.agent import AgentOrchestrator
from app.conversation.repository import ConversationRepository
from app.goals.models import Goal
from app.goals.repository import GoalRepository
from app.memory import MemoryManager, MemoryRepository
from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectTools
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
        self.intent_router = IntentRouter()
        self.orchestrator = AgentOrchestrator(self.root)

        self.memory = MemoryManager(
            MemoryRepository(data / "memory")
        )

        self.goals = GoalRepository(data / "goals.json")

        self.conversation = ConversationRepository(
            data / "conversation" / f"{self.workspace.id}.json"
        )

    def _activate_workspace(self, workspace) -> None:
        self.workspace = workspace
        self.root = Path(workspace.path).resolve(strict=True)
        self.tools = ProjectTools(self.root)
        self.orchestrator = AgentOrchestrator(self.root)
        self.conversation = ConversationRepository(
            self.data_root / "conversation" / f"{workspace.id}.json"
        )

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
                self.conversation.append_turn("user", text)
                self.conversation.append_turn("assistant", response)
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
        intent = self.intent_router.route(text)

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
            result = self.tools.read_file(intent.argument)

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





