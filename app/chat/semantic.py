from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticIntent:
    name: str
    argument: str = ""
    confidence: float = 0.0


_ACKNOWLEDGEMENTS = {
    "ok", "okay", "okey", "k", "kk", "sure", "yeah", "yep", "yup",
    "yes", "yess", "alright", "all right", "fine", "go ahead", "do it",
    "continue", "proceed", "please do", "sounds good", "that works",
    "haan", "ha", "han", "thik", "theek", "thik hai", "theek hai",
    "kar", "kar de", "kar do", "haan kar", "haan kar de",
}

_NEGATIONS = {
    "no", "nope", "nah", "cancel", "stop", "don't", "do not", "not now",
    "leave it", "never mind", "nevermind", "no thanks", "nah bro",
}

_STOP_WORDS = {
    "a", "an", "and", "are", "can", "could", "do", "for", "from", "get",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "tell",
    "the", "this", "to", "what", "with", "you", "your", "we", "would",
}

_INTENT_TERMS = {
    "capabilities": {"feature", "features", "capability", "capabilities", "can", "do"},
    "project_info": {"project", "repo", "repository", "codebase", "workspace", "about", "structure", "understand", "inspect", "inside", "contents"},
    "list_files": {"files", "file", "folders", "folder", "directory", "directories", "inside", "contents", "list", "show"},
    "read_file": {"read", "open", "contents", "inside"},
    "find": {"find", "search", "look", "locate", "where", "grep", "match"},
    "git_status": {"git", "status", "changes", "changed", "clean", "uncommitted", "working", "tree"},
    "git_log": {"git", "log", "commit", "commits", "history", "recent"},
    "git_diff": {"git", "diff", "difference", "changes", "changed", "working", "tree"},
    "goals": {"goal", "goals", "objective", "objectives", "target", "targets"},
    "memory": {"memory", "remembered", "recall", "remember", "forgot", "forget"},
    "permissions": {"permission", "permissions", "access", "allowed", "allow", "modify", "execute", "delete"},
    "run_tests": {"test", "tests", "pytest", "testing", "run"},
    "verify_project": {"verify", "check", "validate", "validation", "project", "codebase", "repo"},
    "verify_git": {"verify", "check", "git", "repository", "repo", "status"},
    "verify_tests": {"verify", "check", "tests", "test", "pytest", "suite"},
    "action_history": {"actions", "history", "done", "did", "taken"},
}


def _normalize(text: str) -> str:
    return " ".join(str(text).strip().casefold().split())


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9']+", " ", text.casefold())
    return {
        token
        for token in normalized.split()
        if token and token not in _STOP_WORDS
    }


def is_acknowledgement(message: str) -> bool:
    text = _normalize(message)
    if text in _ACKNOWLEDGEMENTS:
        return True

    # Accept natural combinations such as "yeah go ahead" or
    # "sure, that's fine" without maintaining a sentence dictionary.
    tokens = _tokens(text)
    acknowledgement_tokens = {
        "ok", "okay", "sure", "yeah", "yep", "yup", "yes", "alright",
        "fine", "proceed", "continue", "please", "haan", "han", "theek",
        "thik", "kar",
    }
    action_words = {
        "delete", "remove", "read", "open", "find", "search", "run",
        "create", "add", "change", "modify", "edit", "switch", "cancel",
    }
    return bool(tokens & acknowledgement_tokens) and not bool(tokens & action_words)


def is_negation(message: str) -> bool:
    text = _normalize(message)
    if text in _NEGATIONS:
        return True
    tokens = _tokens(text)
    return bool(tokens & {"nope", "nah", "cancel", "stop"}) and not bool(
        tokens & {"delete", "remove", "read", "open", "find", "search", "run"}
    )


def _extract_argument(original: str, words: tuple[str, ...]) -> str:
    lowered = original.casefold()
    for phrase in words:
        marker = phrase.casefold()
        index = lowered.find(marker)
        if index >= 0:
            argument = original[index + len(phrase):].strip(" :-,?.\t")
            if argument:
                return argument
    return ""


def classify(message: str) -> SemanticIntent | None:
    """Flexible fallback that classifies by meaning-bearing terms and simple concepts."""
    original = " ".join(str(message).strip().split())
    text = original.casefold()

    if not text:
        return SemanticIntent("empty", confidence=1.0)

    if is_acknowledgement(text):
        return SemanticIntent("context_followup", confidence=0.99)

    if is_negation(text):
        return SemanticIntent("deny", confidence=0.99)

    tokens = _tokens(text)
    if not tokens:
        return None

    scored: list[tuple[float, str]] = []
    for intent, terms in _INTENT_TERMS.items():
        overlap = tokens & terms
        if not overlap:
            continue

        score = len(overlap) / max(3, min(len(terms), 6))

        if intent in {"git_status", "git_log", "git_diff"} and "git" in tokens:
            score += 0.25
        if intent == "list_files" and ({"files", "file", "folder", "folders"} & tokens):
            score += 0.25
        if intent == "list_files" and {"show", "inside"}.issubset(tokens):
            score += 0.25
        if intent == "project_info" and {"repo", "inside"}.issubset(tokens):
            score += 0.30
        if intent == "find" and ({"find", "search", "locate", "look"} & tokens):
            score += 0.35
        if intent == "read_file" and ({"read", "open"} & tokens):
            score += 0.30
        if intent == "run_tests" and ({"test", "tests", "pytest"} & tokens):
            score += 0.30
        if intent.startswith("verify_") and ({"verify", "validate"} & tokens):
            score += 0.30

        scored.append((score, intent))

    if not scored:
        return None

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best_score, best_intent = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if best_score < 0.45 or best_score - second_score < 0.08:
        return None

    argument = ""
    if best_intent == "find":
        argument = _extract_argument(original, ("find", "search for", "search", "look for", "locate"))
    elif best_intent == "read_file":
        argument = _extract_argument(original, ("read", "open"))
    elif best_intent == "memory":
        argument = _extract_argument(original, ("memory", "remember"))

    return SemanticIntent(best_intent, argument=argument, confidence=min(0.99, best_score))
