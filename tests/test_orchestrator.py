from pathlib import Path

from app.agent import AgentOrchestrator


def orchestrator_for(tmp_path: Path) -> AgentOrchestrator:
    return AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )


def test_find_and_inspect_creates_multi_step_plan():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    plan = orchestrator.plan(
        "find where permissions are handled and explain it"
    )

    assert plan is not None
    assert plan.intent == "find_and_inspect"
    assert [step.tool for step in plan.steps] == [
        "search_files",
        "read_relevant_files",
    ]


def test_find_and_inspect_runs_search_then_read():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    response = orchestrator.run(
        "find where permissions are handled and inspect it"
    )

    assert response is not None
    assert "matching file(s)" in response
    assert "app\\permissions" in response
    assert "PermissionLevel" in response


def test_project_diagnosis_creates_plan():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    plan = orchestrator.plan(
        "give me a project overview"
    )

    assert plan is not None
    assert plan.intent == "project_diagnosis"
    assert [step.tool for step in plan.steps] == [
        "project_info",
        "git_status",
        "list_files",
    ]


def test_project_diagnosis_runs_multiple_tools():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    response = orchestrator.run(
        "analyze this project"
    )

    assert response is not None
    assert "Project diagnosis:" in response
    assert "Name: Genos" in response
    assert "Type: Python" in response
    assert "Git status:" in response
    assert "app/" in response


def test_unrecognized_request_has_no_plan():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    assert orchestrator.plan(
        "tell me a joke"
    ) is None


def test_empty_request_has_no_plan():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    assert orchestrator.plan("   ") is None


def test_query_preserves_case():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    plan = orchestrator.plan(
        "find PermissionManager and explain it"
    )

    assert plan is not None
    assert plan.steps[0].argument == "PermissionManager"


def test_issue_diagnosis_creates_plan():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    plan = orchestrator.plan(
        "what is wrong with authentication"
    )

    assert plan is not None
    assert plan.intent == "issue_diagnosis"
    assert [step.tool for step in plan.steps] == [
        "project_info",
        "git_status",
        "list_files",
        "search_files",
    ]
    assert plan.steps[-1].argument == "authentication"


def test_issue_diagnosis_runs_evidence_gathering():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    response = orchestrator.run(
        "what is wrong with authentication"
    )

    assert response is not None
    assert "Project diagnosis:" in response
    assert "Evidence:" in response
    assert "Relevant evidence for" in response
    assert "Inspected evidence:" in response


def test_issue_diagnosis_handles_failure_question():
    orchestrator = AgentOrchestrator(
        Path(__file__).resolve().parents[1]
    )

    plan = orchestrator.plan(
        "why is this project failing"
    )

    assert plan is not None
    assert plan.intent == "issue_diagnosis"
    assert plan.steps[-1].tool != "search_files"


def test_runtime_routes_natural_diagnosis(tmp_path: Path):
    from app.chat import GenosRuntime

    runtime = GenosRuntime(
        Path(__file__).resolve().parents[1],
        data_root=tmp_path / "data",
    )

    response = runtime.handle(
        "what is wrong with authentication"
    )

    assert "Project diagnosis:" in response
    assert "Evidence:" in response
