from .runtime import GenosRuntime, main
from .intent import IntentRouter
from .semantic import classify


_original_route = IntentRouter.route


def _semantic_route(self, message: str):
    """Keep deterministic routes first, then use flexible semantic fallback."""
    intent = _original_route(self, message)

    if intent.name != "unknown":
        return intent

    semantic = classify(message)

    if semantic is None:
        return intent

    return type(intent)(semantic.name, semantic.argument)


IntentRouter.route = _semantic_route


__all__ = [
    "GenosRuntime",
    "main",
]
