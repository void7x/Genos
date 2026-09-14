from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectInfo:
    path: str
    name: str
    project_type: str
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    source_dirs: tuple[str, ...]
    test_dirs: tuple[str, ...]
    readme: str | None
    is_git_repo: bool
    git_branch: str | None
    git_clean: bool | None
    run_commands: tuple[str, ...]
    test_commands: tuple[str, ...]


class ProjectInspector:
    def inspect(self, path: str | Path) -> ProjectInfo:
        root = Path(path).expanduser().resolve(strict=True)

        if not root.is_dir():
            raise ValueError(f"Project is not a directory: {root}")

        root_files = {
            item.name.casefold()
            for item in root.iterdir()
            if item.is_file()
        }

        root_dirs = {
            item.name.casefold()
            for item in root.iterdir()
            if item.is_dir()
        }

        code_files = {
            item.name.casefold()
            for item in root.rglob("*")
            if item.is_file()
            and not any(
                part.casefold()
                in {
                    ".git",
                    ".venv",
                    "venv",
                    "__pycache__",
                    ".pytest_cache",
                    "node_modules",
                }
                for part in item.relative_to(root).parts
            )
        }

        languages = self._languages(code_files)
        project_type = self._project_type(
            root_files,
            root_dirs,
            code_files,
        )
        frameworks = self._frameworks(
            root,
            root_files,
            project_type,
        )

        source_dirs = tuple(
            name
            for name in (
                "src",
                "app",
                "lib",
                "server",
                "backend",
                "frontend",
            )
            if name in root_dirs
        )

        test_dirs = tuple(
            name
            for name in (
                "tests",
                "test",
                "__tests__",
            )
            if name in root_dirs
        )

        readme = next(
            (
                name
                for name in (
                    "README.md",
                    "README.rst",
                    "README.txt",
                    "README",
                )
                if (root / name).is_file()
            ),
            None,
        )

        is_git_repo = (root / ".git").exists()
        git_branch = (
            self._git(root, "branch", "--show-current")
            if is_git_repo
            else None
        )

        git_status = (
            self._git(root, "status", "--porcelain")
            if is_git_repo
            else None
        )

        git_clean = (
            git_status == ""
            if is_git_repo and git_status is not None
            else None
        )

        run_commands, test_commands = self._commands(
            root,
            root_files,
            project_type,
        )

        return ProjectInfo(
            path=str(root),
            name=root.name or str(root),
            project_type=project_type,
            languages=languages,
            frameworks=frameworks,
            source_dirs=source_dirs,
            test_dirs=test_dirs,
            readme=readme,
            is_git_repo=is_git_repo,
            git_branch=git_branch,
            git_clean=git_clean,
            run_commands=run_commands,
            test_commands=test_commands,
        )

    @staticmethod
    def _languages(files: set[str]) -> tuple[str, ...]:
        found: list[str] = []

        if any(name.endswith(".py") for name in files):
            found.append("Python")
        if any(name.endswith((".js", ".jsx", ".mjs", ".cjs")) for name in files):
            found.append("JavaScript")
        if any(name.endswith((".ts", ".tsx")) for name in files):
            found.append("TypeScript")
        if any(name.endswith(".java") for name in files):
            found.append("Java")
        if any(name.endswith(".go") for name in files):
            found.append("Go")
        if any(name.endswith(".rs") for name in files):
            found.append("Rust")
        if any(name.endswith(".cs") for name in files):
            found.append("C#")
        if any(name.endswith((".cpp", ".cc", ".cxx", ".hpp", ".h")) for name in files):
            found.append("C/C++")

        return tuple(found)

    @staticmethod
    def _project_type(
        files: set[str],
        dirs: set[str],
        code_files: set[str],
    ) -> str:
        if (
            "pyproject.toml" in files
            or "requirements.txt" in files
            or "setup.py" in files
        ):
            return "Python"

        if "package.json" in files:
            if "next.config.js" in files or "next.config.mjs" in files:
                return "Next.js"
            return "Node.js"

        if (
            "pom.xml" in files
            or "build.gradle" in files
            or "build.gradle.kts" in files
        ):
            return "Java"

        if "go.mod" in files:
            return "Go"

        if "cargo.toml" in files:
            return "Rust"

        if "docker-compose.yml" in files or "docker-compose.yaml" in files:
            return "Docker"

        if "dockerfile" in files:
            return "Containerized"

        if any(name.endswith(".py") for name in code_files):
            return "Python"

        if any(
            name.endswith((".ts", ".tsx", ".js", ".jsx"))
            for name in code_files
        ):
            return "JavaScript/TypeScript"

        if "src" in dirs:
            return "Source Project"

        return "Unknown"

    @staticmethod
    def _frameworks(
        root: Path,
        files: set[str],
        project_type: str,
    ) -> tuple[str, ...]:
        found: list[str] = []

        if project_type == "Python":
            if (root / "manage.py").is_file():
                found.append("Django")

            if (root / "requirements.txt").is_file():
                try:
                    text = (
                        root / "requirements.txt"
                    ).read_text(
                        encoding="utf-8",
                        errors="ignore",
                    ).casefold()
                except OSError:
                    text = ""

                checks = (
                    ("fastapi", "FastAPI"),
                    ("flask", "Flask"),
                    ("django", "Django"),
                    ("pytest", "pytest"),
                )

                for marker, name in checks:
                    if marker in text and name not in found:
                        found.append(name)

        if "package.json" in files:
            try:
                package = json.loads(
                    (root / "package.json").read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )
            except (OSError, json.JSONDecodeError):
                package = {}

            deps = {}
            deps.update(package.get("dependencies", {}) or {})
            deps.update(package.get("devDependencies", {}) or {})

            checks = (
                ("react", "React"),
                ("vue", "Vue"),
                ("@angular/core", "Angular"),
                ("express", "Express"),
                ("next", "Next.js"),
                ("vite", "Vite"),
            )

            for marker, name in checks:
                if marker in deps and name not in found:
                    found.append(name)

        if "docker-compose.yml" in files or "docker-compose.yaml" in files:
            found.append("Docker Compose")

        return tuple(found)

    @staticmethod
    def _commands(
        root: Path,
        files: set[str],
        project_type: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        run: list[str] = []
        test: list[str] = []

        if "package.json" in files:
            try:
                package = json.loads(
                    (root / "package.json").read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )
            except (OSError, json.JSONDecodeError):
                package = {}

            scripts = package.get("scripts", {}) or {}

            if "dev" in scripts:
                run.append("npm run dev")
            elif "start" in scripts:
                run.append("npm start")

            if "test" in scripts:
                test.append("npm test")

        if project_type == "Python":
            if (root / "tests").is_dir():
                test.append("python -m pytest")

            if (root / "app" / "main.py").is_file():
                run.append("python -m app.main")

        if "docker-compose.yml" in files:
            run.append("docker compose up")
        elif "docker-compose.yaml" in files:
            run.append("docker compose up")

        if (root / "Makefile").is_file():
            run.append("make run")
            test.append("make test")

        return tuple(dict.fromkeys(run)), tuple(dict.fromkeys(test))

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""

        if result.returncode != 0:
            return ""

        return result.stdout.strip()
