/**
 * PROTOTYPE SCENERY ONLY.
 *
 * The floating-companion concept needs *something* to float above in a
 * browser demo, so the shell renders a decorative editor behind Genos.
 * These constants are stage props — they are NOT Genos domain data, they are
 * not read by any Genos component, and they are not connected to the service
 * layer or the mock engine. A real desktop shell removes DesktopStage
 * entirely; nothing else changes.
 */

export const SCENE_TITLE = 'resolver.py — editor'

export const SCENE_META = 'local · read-only scenery'

export const SCENE_FILES = [
  'agent/multi_step.py',
  'chat/runtime.py',
  'memory/manager.py',
  'memory/resolver.py',
  'verification/engine.py',
  'tests/memory/test_resolver.py',
  'tests/verification/test_engine.py',
]

export const SCENE_CODE = [
  'from dataclasses import dataclass',
  'from typing import Iterable, Sequence',
  '',
  'from memory.manager import MemoryPool',
  'from workspace import WorkspaceScope',
  '',
  '',
  '@dataclass(frozen=True)',
  'class Resolution:',
  '    """A single resolved memory with its score."""',
  '',
  '    memory_id: str',
  '    score: float',
  '',
  '',
  'def resolve_memories(',
  '    workspace_id: str,',
  '    query: str,',
  '    limit: int = 8,',
  ') -> Sequence[Resolution]:',
  '    """Resolve project-scoped memories for a query."""',
  '    candidates = _candidate_pool(workspace_id)',
  '    scored = [_score(query, c) for c in candidates]',
  '    ranked = sorted(zip(scored, candidates), reverse=True)',
  '    return [c for _, c in ranked[:limit]]',
  '',
  '',
  'def _candidate_pool(workspace_id: str) -> Iterable[MemoryPool]:',
  '    scope = WorkspaceScope.load(workspace_id)',
  '    return scope.iter_memories(include_shadowed=True)',
]
