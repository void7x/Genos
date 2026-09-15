from pathlib import Path

from app.tools.project_tools import ProjectTools


def test_search_files_matches_filename(tmp_path: Path):
    target = tmp_path / "workflow.py"
    target.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    result = ProjectTools(tmp_path).search_files(
        "workflow.py"
    )

    assert result.success
    assert "workflow.py" in result.output
