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


