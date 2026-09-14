from pathlib import Path

from app.workspace import ProjectInspector


def test_inspector_detects_python_project(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text(
        "pytest\nfastapi\n",
        encoding="utf-8",
    )

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Python"
    assert "Python" in info.languages
    assert "FastAPI" in info.frameworks
    assert "pytest" in info.frameworks
    assert info.source_dirs == ("app",)
    assert info.test_dirs == ("tests",)
    assert info.readme == "README.md"
    assert info.test_commands == ("python -m pytest",)
    assert info.run_commands == ()


def test_inspector_detects_nested_python_code(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text(
        "print('Genos')",
        encoding="utf-8",
    )

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Python"
    assert info.languages == ("Python",)


def test_inspector_detects_node_react_vite(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.jsx").write_text(
        "export default function App() {}",
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"react":"1"},"devDependencies":{"vite":"1"},'
        '"scripts":{"dev":"vite","test":"vitest"}}',
        encoding="utf-8",
    )

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Node.js"
    assert info.languages == ("JavaScript",)
    assert set(info.frameworks) == {"React", "Vite"}
    assert info.source_dirs == ("src",)
    assert info.run_commands == ("npm run dev",)
    assert info.test_commands == ("npm test",)


def test_inspector_detects_git_state(tmp_path: Path):
    (tmp_path / ".git").mkdir()

    info = ProjectInspector().inspect(tmp_path)

    assert info.is_git_repo is True
    assert info.git_branch is None or isinstance(info.git_branch, str)
    assert info.git_clean in {True, False, None}


def test_inspector_rejects_file(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")

    try:
        ProjectInspector().inspect(file_path)
    except ValueError as exc:
        assert "not a directory" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_inspector_reads_java_project(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    (tmp_path / "Main.java").write_text("class Main {}", encoding="utf-8")

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Java"
    assert info.languages == ("Java",)


def test_inspector_detects_docker_compose(tmp_path: Path):
    (tmp_path / "docker-compose.yml").write_text(
        "services: {}",
        encoding="utf-8",
    )

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Docker"
    assert "Docker Compose" in info.frameworks
    assert info.run_commands == ("docker compose up",)


def test_inspector_handles_unknown_project(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")

    info = ProjectInspector().inspect(tmp_path)

    assert info.project_type == "Unknown"
    assert info.languages == ()
    assert info.frameworks == ()
    assert info.run_commands == ()
    assert info.test_commands == ()
