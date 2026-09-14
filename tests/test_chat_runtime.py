from pathlib import Path

from app.chat import GenosRuntime


def runtime_for(tmp_path: Path) -> GenosRuntime:
    return GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )


def test_help(tmp_path: Path):
    response = runtime_for(tmp_path).handle("help")

    assert "files" in response
    assert "Git status and history" in response


def test_project_info(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "what is this project"
    )

    assert "Name: Genos" in response
    assert "Type: Python" in response
    assert "Python" in response


def test_list_files(tmp_path: Path):
    response = runtime_for(tmp_path).handle("list files")

    assert "app/" in response
    assert "tests/" in response


def test_read_readme(tmp_path: Path):
    response = runtime_for(tmp_path).handle("read readme")

    assert "# Genos" in response


def test_find_files(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "find ProjectTools"
    )

    assert "project_tools.py" in response


def test_git_status(tmp_path: Path):
    response = runtime_for(tmp_path).handle("git status")

    assert "app/chat/" in response


def test_git_log(tmp_path: Path):
    response = runtime_for(tmp_path).handle("git log")

    assert "Implement permissions v1" in response


def test_memory_is_workspace_scoped(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle(
        "remember Genos uses workspace-scoped memory"
    )

    assert "Remembered:" in response

    search = runtime.handle("memory workspace-scoped")

    assert "workspace-scoped memory" in search


def test_goals_are_workspace_scoped(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle(
        "goal Build the Genos chatbot"
    )

    assert "Build the Genos chatbot" in response

    goals = runtime.handle("goals")

    assert "Build the Genos chatbot" in goals


def test_permissions(tmp_path: Path):
    response = runtime_for(tmp_path).handle("permissions")

    assert "READ: True" in response
    assert "SAFE_WRITE: False" in response
    assert "EXECUTE: False" in response
    assert "DESTRUCTIVE: False" in response


def test_unknown_command(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "do something magical"
    )

    assert "don't understand" in response


def test_conversation_is_persisted(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    runtime.handle("hello")
    runtime.handle("git status")

    history = runtime.conversation.load()

    assert history
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "assistant"




def test_workspace_switching(tmp_path):
    from app.chat.runtime import GenosRuntime

    genos = tmp_path / "Genos"
    mailingguard = tmp_path / "MailingGuard"

    genos.mkdir()
    mailingguard.mkdir()

    runtime = GenosRuntime(genos, data_root=tmp_path / "data")
    runtime.workspace_manager.attach(mailingguard)

    listed = runtime.handle("list my workspaces")
    assert "Genos" in listed
    assert "MailingGuard" in listed

    switched = runtime.handle("go to MailingGuard")

    assert "Switched workspace." in switched
    assert runtime.workspace.name == "MailingGuard"


def test_workspace_switching_preserves_active_context(tmp_path):
    from app.chat.runtime import GenosRuntime

    genos = tmp_path / "Genos"
    mailingguard = tmp_path / "MailingGuard"

    genos.mkdir()
    mailingguard.mkdir()

    runtime = GenosRuntime(genos, data_root=tmp_path / "data")
    runtime.workspace_manager.attach(mailingguard)

    runtime.handle("switch to MailingGuard")

    assert runtime.workspace.name == "MailingGuard"
    assert runtime.root == mailingguard.resolve()
    assert runtime.tools.root == mailingguard.resolve()


def test_safe_write_permission_and_write(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    denied = runtime.handle(
        "write file test_output.txt :: hello"
    )
    assert "SAFE_WRITE" in denied

    runtime.handle("grant safe write")

    created = runtime.handle(
        "write file test_output.txt :: hello"
    )
    assert "test_output.txt" in created


def test_execute_permission_and_command(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    denied = runtime.handle("execute python --version")
    assert "EXECUTE" in denied

    runtime.handle("grant execute")

    result = runtime.handle("execute python --version")
    assert "Python" in result




def test_verify_file_runtime(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    target = Path(runtime.root) / "verification_target.txt"
    target.write_text("verified", encoding="utf-8")

    response = runtime.handle(
        "verify file verification_target.txt"
    )

    assert "VERIFICATION: PASSED" in response
    assert "Verified file" in response


def test_verify_project_runtime(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    response = runtime.handle("verify project")

    assert "VERIFICATION: PASSED" in response

def test_natural_task_plans_project_status_notes(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "create a notes file with the current project status"
    )

    assert "Plan:" in response
    assert "SAFE_WRITE" in response
    assert "notes/project_status.md" in response


def test_natural_task_executes_after_approval(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("grant safe write")

    response = runtime.workflow.plan_write(
        "notes/workflow_status.md",
        "# Project Status\n\nName: Genos\nType: Python\n",
    )

    assert "SAFE_WRITE" in response

    result = runtime.handle("approve")

    target = (
        Path(runtime.root)
        / "notes"
        / "workflow_status.md"
    )

    assert "ACT: SUCCESS" in result
    assert "VERIFY: PASSED" in result
    assert "REMEMBER: Saved" in result
    assert target.exists()

    content = target.read_text(encoding="utf-8")

    assert "# Project Status" in content
    assert "Name: Genos" in content
    assert "Type: Python" in content

def test_natural_task_executes_after_approval(tmp_path: Path):
    runtime = GenosRuntime(
        tmp_path,
        data_root=tmp_path / "data",
    )

    runtime.handle("grant safe write")

    response = runtime.workflow.plan_write(
        "notes/workflow_status.md",
        "# Project Status\n\nName: Genos\nType: Python\n",
    )

    assert "SAFE_WRITE" in response

    result = runtime.handle("approve")

    target = (
        Path(runtime.root)
        / "notes"
        / "workflow_status.md"
    )

    assert "ACT: SUCCESS" in result
    assert "VERIFY: PASSED" in result
    assert "REMEMBER: Saved" in result
    assert target.exists()

    content = target.read_text(encoding="utf-8")

    assert "# Project Status" in content
    assert "Name: Genos" in content
    assert "Type: Python" in content

def test_natural_task_stops_on_existing_target(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    target = Path(runtime.root) / "notes" / "project_status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing", encoding="utf-8")

    response = runtime.handle(
        "create a notes file with the current project status"
    )

    assert "Target already exists" in response
    assert "will not overwrite" in response




