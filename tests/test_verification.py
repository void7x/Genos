from pathlib import Path

from app.permissions import PermissionLevel, PermissionManager
from app.tools import ProjectActionTools
from app.verification import VerificationEngine


def test_verify_file_exists(tmp_path: Path):
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = VerificationEngine(tmp_path).verify_file("note.txt")

    assert result.success is True
    assert "Verified file" in result.summary


def test_verify_file_content(tmp_path: Path):
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = VerificationEngine(tmp_path).verify_file(
        "note.txt",
        expected_content="hello",
    )

    assert result.success is True
    assert "expected content matches" in result.checks


def test_verify_file_detects_content_mismatch(tmp_path: Path):
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = VerificationEngine(tmp_path).verify_file(
        "note.txt",
        expected_content="wrong",
    )

    assert result.success is False
    assert "mismatch" in result.summary


def test_verify_missing_file(tmp_path: Path):
    result = VerificationEngine(tmp_path).verify_file(
        "missing.txt"
    )

    assert result.success is False


def test_verify_git(tmp_path: Path):
    import subprocess

    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    result = VerificationEngine(tmp_path).verify_git()

    assert result.success is True
    assert "Git verification complete" in result.summary


def test_verify_project(tmp_path: Path):
    result = VerificationEngine(tmp_path).verify_project()

    assert result.success is True
    assert "Project verification passed" in result.summary


def test_verify_tests_requires_execute(tmp_path: Path):
    permissions = PermissionManager()
    actions = ProjectActionTools(tmp_path, permissions)

    result = VerificationEngine(
        tmp_path,
        actions,
    ).verify_tests()

    assert result.success is False
    assert "EXECUTE" in result.summary
    assert result.checks == ("pytest command executed",)
