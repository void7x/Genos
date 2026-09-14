from pathlib import Path
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CodingTask:
    action: str
    target: str
    details: str = ""


class CodingTaskExecutor:
    """Prepare deterministic, reviewable coding edits."""

    def __init__(self, root):
        self.root = Path(root).expanduser().resolve(strict=True)

    def prepare(self, action, target, details=""):
        if action == "create_file":
            return (target, details) if details else None

        if action == "add_logging":
            return self._add_logging(target)

        return None

    def _add_logging(self, target):
        path = (self.root / target).resolve()

        try:
            path.relative_to(self.root)
        except ValueError:
            return None

        if not path.exists() or not path.is_file():
            return None

        if path.suffix.casefold() != ".py":
            return None

        content = path.read_text(encoding="utf-8")

        if "import logging" not in content:
            content = "import logging\n" + content

        if "logger = logging.getLogger(__name__)" not in content:
            lines = content.splitlines()
            insert_at = 0

            while insert_at < len(lines):
                line = lines[insert_at].strip()

                if (
                    not line
                    or line.startswith("#")
                    or line.startswith("from __future__")
                    or line.startswith("import ")
                    or line.startswith("from ")
                ):
                    insert_at += 1
                    continue

                break

            lines.insert(
                insert_at,
                "logger = logging.getLogger(__name__)",
            )

            content = "\n".join(lines)
            if content:
                content += "\n"

        lines = content.splitlines()

        for index, line in enumerate(lines):
            match = re.match(
                r"^(\s*)def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                line,
            )

            if not match:
                continue

            indent = match.group(1) + "    "
            function_name = match.group(2)

            next_index = index + 1

            while (
                next_index < len(lines)
                and not lines[next_index].strip()
            ):
                next_index += 1

            if (
                next_index < len(lines)
                and "logger." in lines[next_index]
            ):
                return target, "\n".join(lines) + "\n"

            lines.insert(
                index + 1,
                f'{indent}logger.debug("Entering {function_name}")',
            )

            return target, "\n".join(lines) + "\n"

        return target, content
