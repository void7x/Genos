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

    assert "app/chat/" in response


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
