from pathlib import Path

from app.chat import GenosRuntime
from app.chat.intent import IntentRouter


def runtime_for(tmp_path: Path) -> GenosRuntime:
    return GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )


def test_natural_project_question(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "tell me about this project"
    )

    assert "Name: Genos" in response
    assert "Type: Python" in response


def test_natural_features_question(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "what features do you have?"
    )

    assert "Understand the active project" in response
    assert "Store and search project memory" in response


def test_natural_file_request(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "show me the project files"
    )

    assert "app/" in response
    assert "tests/" in response


def test_natural_search_request(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "search for PermissionManager"
    )

    assert "manager.py" in response


def test_natural_git_request(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "are there any uncommitted changes?"
    )

    assert response.strip()


def test_natural_goals_request(tmp_path: Path):
    runtime = runtime_for(tmp_path)

    runtime.handle("goal Build the real agent")

    response = runtime.handle(
        "what are my goals?"
    )

    assert "Build the real agent" in response


def test_natural_permissions_request(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "what can you modify?"
    )

    assert "SAFE_WRITE: False" in response
    assert "EXECUTE: False" in response


def test_natural_readme_request(tmp_path: Path):
    response = runtime_for(tmp_path).handle(
        "please read the readme"
    )

    assert "# Genos" in response


def test_intent_router_project_variants():
    router = IntentRouter()

    assert router.route(
        "tell me about this project"
    ).name == "project_info"

    assert router.route(
        "describe this project"
    ).name == "project_info"


def test_intent_router_feature_variants():
    router = IntentRouter()

    assert router.route(
        "what can you do"
    ).name == "capabilities"

    assert router.route(
        "what are your features"
    ).name == "capabilities"


def test_intent_router_git_variants():
    router = IntentRouter()

    assert router.route(
        "show me the git status"
    ).name == "git_status"

    assert router.route(
        "do I have uncommitted changes?"
    ).name == "git_status"


def test_intent_router_preserves_argument_case():
    router = IntentRouter()

    intent = router.route(
        "goal Build the Genos Chatbot"
    )

    assert intent.name == "goal"
    assert intent.argument == "Build the Genos Chatbot"


def test_permission_synonyms():
    router = IntentRouter()

    assert router.route("grant safe write").name == "grant_safe_write"
    assert router.route("give me permission to edit files").name == "grant_safe_write"
    assert router.route("allow me to modify files").name == "grant_safe_write"

    assert router.route("grant execute").name == "grant_execute"
    assert router.route("let me run commands").name == "grant_execute"

    assert router.route("grant destructive").name == "grant_destructive"
    assert router.route("let me delete files").name == "grant_destructive"


def test_workspace_synonyms():
    router = IntentRouter()

    assert router.route("list my workspaces").name == "workspace_list"
    assert router.route("what projects are available").name == "workspace_list"

    assert router.route("go to MailingGuard").name == "workspace_switch"
    assert router.route("work on MailingGuard").name == "workspace_switch"
    assert router.route("move to MailingGuard").name == "workspace_switch"


def test_action_synonyms():
    router = IntentRouter()

    assert router.route("remove file notes.txt").name == "delete_file"
    assert router.route("run the tests").name == "run_tests"
    assert router.route("verify the project").name == "verify_project"
    assert router.route("verify file README.md").name == "verify_file"



