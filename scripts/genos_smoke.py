from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def main() -> None:
    root = ROOT

    with tempfile.TemporaryDirectory(prefix="genos-smoke-") as temp:
        temp_root = Path(temp)

        print("=== GENOS SMOKE TEST ===")
        print(f"Workspace: {root}")

        workspace_repo = WorkspaceRepository(
            temp_root / "workspaces.json"
        )
        workspace_manager = WorkspaceManager(workspace_repo)
        workspace = workspace_manager.attach(root)

        assert workspace.path == str(root)
        assert workspace_manager.current() == workspace
        print("[PASS] workspace attach/current")

        info = ProjectInspector().inspect(root)

        assert info.path == str(root)
        assert info.is_git_repo is True
        assert info.git_branch == "main"
        assert "Python" in info.languages
        assert "app" in info.source_dirs
        assert "tests" in info.test_dirs

        print(
            "[PASS] project inspection",
            f"({info.project_type}, {', '.join(info.languages)})",
        )

        tools = ProjectTools(root)

        files = tools.list_files()
        assert files.success is True
        assert "app/" in files.output
        assert "tests/" in files.output

        readme = tools.read_file("README.md")
        assert readme.success is True
        assert "# Genos" in readme.output

        search = tools.search_files("ProjectTools")
        assert search.success is True
        assert any(
            match.endswith("project_tools.py")
            for match in search.output.splitlines()
        )

        status = tools.git_status()
        assert status.success is True

        log = tools.git_log(3)
        assert log.success is True
        assert log.output

        print("[PASS] project tools")

        permissions = PermissionManager()

        assert permissions.is_allowed(PermissionLevel.READ)
        assert not permissions.is_allowed(PermissionLevel.SAFE_WRITE)
        assert not permissions.is_allowed(PermissionLevel.EXECUTE)
        assert not permissions.is_allowed(PermissionLevel.DESTRUCTIVE)

        permissions.grant(PermissionLevel.SAFE_WRITE)
        assert permissions.is_allowed(PermissionLevel.SAFE_WRITE)

        permissions.revoke(PermissionLevel.SAFE_WRITE)
        assert not permissions.is_allowed(PermissionLevel.SAFE_WRITE)

        print("[PASS] permission policy")

        memory = MemoryManager(
            MemoryRepository(temp_root / "memory")
        )

        saved_memory = memory.add(
            workspace.id,
            "Genos is the local-first project companion.",
            ("identity", "project"),
        )

        assert memory.search(workspace.id, "local-first")
        assert memory.search(workspace.id, "project")
        assert saved_memory.workspace_id == workspace.id

        print("[PASS] workspace memory")

        goals = GoalRepository(temp_root / "goals.json")

        saved_goal = goals.add(
            Goal(
                title="Make Genos understand projects",
                priority="high",
            ),
            workspace.id,
        )

        loaded_goals = goals.list(workspace.id)

        assert loaded_goals == [saved_goal]

        print("[PASS] workspace goals")

        print()
        print("GENOS SMOKE TEST: PASSED")
        print(
            "Components exercised together:"
        )
        print(
            "  workspace -> inspector -> tools -> "
            "permissions -> memory -> goals"
        )


if __name__ == "__main__":
    main()
