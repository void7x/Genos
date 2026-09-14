from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Memory:
    id: str
    workspace_id: str
    content: str
    tags: tuple[str, ...]
    created_at: str
    updated_at: str


class MemoryRepository:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, workspace_id: str) -> Path:
        normalized = str(workspace_id).strip()

        if not normalized:
            raise ValueError("Workspace ID cannot be empty.")

        # Never use caller-controlled workspace IDs directly as path components.
        safe_name = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return self.root / safe_name / "memory.json"

    def load(self, workspace_id: str) -> list[Memory]:
        normalized_workspace = str(workspace_id).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized_workspace)

        if not path.exists():
            return []

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(raw, list):
            return []

        memories: list[Memory] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            try:
                tags = item.get("tags", [])

                if not isinstance(tags, list):
                    tags = []

                memories.append(
                    Memory(
                        id=str(item.get("id", "")),
                        workspace_id=str(item.get("workspace_id", "")),
                        content=str(item.get("content", "")).strip(),
                        tags=tuple(
                            str(tag).strip()
                            for tag in tags
                            if str(tag).strip()
                        ),
                        created_at=str(item.get("created_at", "")),
                        updated_at=str(item.get("updated_at", "")),
                    )
                )
            except (TypeError, ValueError):
                continue

        return [
            memory
            for memory in memories
            if memory.id
            and memory.workspace_id == normalized_workspace
            and memory.content
        ]

    def save(self, workspace_id: str, memories: list[Memory]) -> None:
        normalized_workspace = str(workspace_id).strip()

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        path = self._path(normalized_workspace)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = [asdict(memory) for memory in memories]

        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class MemoryManager:
    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    def list(self, workspace_id: str) -> list[Memory]:
        return self.repository.load(workspace_id)

    def add(
        self,
        workspace_id: str,
        content: str,
        tags: tuple[str, ...] = (),
    ) -> Memory:
        normalized_workspace = str(workspace_id).strip()
        normalized_content = " ".join(str(content).strip().split())

        if not normalized_workspace:
            raise ValueError("Workspace ID cannot be empty.")

        if not normalized_content:
            raise ValueError("Memory content cannot be empty.")

        normalized_tags = tuple(
            dict.fromkeys(
                tag.strip().casefold()
                for tag in tags
                if tag.strip()
            )
        )

        memories = self.repository.load(normalized_workspace)

        for memory in memories:
            if memory.content.casefold() == normalized_content.casefold():
                return memory

        now = datetime.now(timezone.utc).isoformat()

        memory = Memory(
            id=uuid.uuid4().hex[:16],
            workspace_id=normalized_workspace,
            content=normalized_content,
            tags=normalized_tags,
            created_at=now,
            updated_at=now,
        )

        memories.append(memory)
        self.repository.save(normalized_workspace, memories)

        return memory

    def search(self, workspace_id: str, query: str) -> list[Memory]:
        normalized_query = " ".join(str(query).strip().casefold().split())

        if not normalized_query:
            return []

        terms = set(normalized_query.split())
        memories = self.repository.load(workspace_id)

        scored: list[tuple[int, int, Memory]] = []

        for index, memory in enumerate(memories):
            text = memory.content.casefold()
            tag_text = " ".join(memory.tags)
            haystack = f"{text} {tag_text}"

            score = sum(
                1
                for term in terms
                if term in haystack
            )

            if score:
                scored.append((score, index, memory))

        scored.sort(key=lambda item: (-item[0], item[1]))

        return [item[2] for item in scored]

    def delete(self, workspace_id: str, memory_id: str) -> bool:
        normalized_workspace = str(workspace_id).strip()
        normalized_id = str(memory_id).strip()

        memories = self.repository.load(normalized_workspace)

        remaining = [
            memory
            for memory in memories
            if memory.id != normalized_id
        ]

        if len(remaining) == len(memories):
            return False

        self.repository.save(normalized_workspace, remaining)
        return True
