from pathlib import Path

import pytest

from app.conversation.repository import ConversationRepository


def test_missing_history_is_empty(tmp_path: Path):
    repo = ConversationRepository(tmp_path / "conversation.json")

    assert repo.load() == []


def test_history_persists_and_reloads(tmp_path: Path):
    path = tmp_path / "conversation.json"
    repo = ConversationRepository(path)

    history = [
        {"role": "user", "content": "We are building Mereum."},
        {"role": "assistant", "content": "Yes, we are."},
    ]

    repo.save(history)

    assert ConversationRepository(path).load() == history


def test_history_is_bounded(tmp_path: Path):
    path = tmp_path / "conversation.json"
    repo = ConversationRepository(path, max_messages=4)

    history = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
        {"role": "assistant", "content": "four"},
        {"role": "user", "content": "five"},
        {"role": "assistant", "content": "six"},
    ]

    repo.save(history)

    assert ConversationRepository(path, max_messages=4).load() == history[-4:]


def test_append_turn(tmp_path: Path):
    repo = ConversationRepository(tmp_path / "conversation.json")

    repo.append_turn("Hello", "Hi Sahil.")

    assert repo.load() == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi Sahil."},
    ]


def test_invalid_records_are_ignored(tmp_path: Path):
    path = tmp_path / "conversation.json"
    path.write_text(
        """
        [
          {"role": "user", "content": "valid"},
          {"role": "system", "content": "ignore"},
          {"role": "assistant", "content": ""},
          {"broken": true}
        ]
        """,
        encoding="utf-8",
    )

    assert ConversationRepository(path).load() == [
        {"role": "user", "content": "valid"}
    ]


def test_invalid_max_messages_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        ConversationRepository(tmp_path / "conversation.json", max_messages=0)
