from app.chat.intent import IntentRouter


def test_acknowledgement_is_not_unknown():
    router = IntentRouter()

    for message in (
        "ok",
        "yeah go ahead",
        "sure",
        "haan kar de",
        "that's fine",
    ):
        assert router.route(message).name == "context_followup"


def test_natural_project_requests_do_not_require_exact_phrasing():
    router = IntentRouter()

    assert router.route("could you show me what is inside this repo?").name in {
        "project_info",
        "list_files",
    }
    assert router.route("can you check the git changes for me").name == "git_status"
    assert router.route("please look for the auth implementation").name == "find"
    assert router.route("open the config file for me").name == "read_file"
    assert router.route("can you run the tests now").name == "run_tests"


def test_unknown_stays_unknown_when_meaning_is_ambiguous():
    router = IntentRouter()

    assert router.route("banana spaceship maybe").name == "unknown"
