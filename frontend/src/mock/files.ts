/**
 * Mock: file previews and diffs.
 *
 * DEMO DATA ONLY — the prototype never reads or writes real files.
 */
import type { FileDiff } from '../types'

export const mockResolverSnippet = `def resolve_memories(workspace_id, query, limit=8):
    """Resolve project-scoped memories for a query."""
    candidates = _candidate_pool(workspace_id)
    scored = [_score(query, c) for c in candidates]
    ranked = sorted(zip(scored, candidates), reverse=True)
    return [c for _, c in ranked[:limit]]`

export const mockResolverDiff: FileDiff = {
  path: 'app/memory/resolver.py',
  change: 'modified',
  language: 'python',
  lines: [
    { type: 'context', oldNo: 71, newNo: 71, text: 'def resolve_memories(workspace_id, query, limit=8):' },
    { type: 'context', oldNo: 72, newNo: 72, text: '    """Resolve project-scoped memories for a query."""' },
    { type: 'context', oldNo: 73, newNo: 73, text: '    candidates = _candidate_pool(workspace_id)' },
    { type: 'remove', oldNo: 74, text: '    scored = [_score(query, c) for c in candidates]' },
    { type: 'remove', oldNo: 75, text: '    ranked = sorted(zip(scored, candidates), reverse=True)' },
    { type: 'add', newNo: 74, text: '    scored = {_score(query, c): c.id for c in candidates}' },
    { type: 'add', newNo: 75, text: '    unique = _dedupe_by_identity(candidates)' },
    { type: 'add', newNo: 76, text: '    ranked = sorted(unique, key=lambda c: scored[c.id], reverse=True)' },
    { type: 'context', oldNo: 76, newNo: 77, text: '    return [c for _, c in ranked[:limit]]' },
  ],
}

export const mockTestDiff: FileDiff = {
  path: 'tests/memory/test_resolver.py',
  change: 'modified',
  language: 'python',
  lines: [
    { type: 'context', oldNo: 116, newNo: 116, text: 'def test_resolver_returns_unique_memories(seed_pool):' },
    { type: 'remove', oldNo: 117, text: '    result = resolve_memories("ws_1", "sandbox policy", limit=4)' },
    { type: 'remove', oldNo: 118, text: '    assert len(result) == 4' },
    { type: 'add', newNo: 117, text: '    result = resolve_memories("ws_1", "sandbox policy", limit=4)' },
    { type: 'add', newNo: 118, text: '    ids = [m.id for m in result]' },
    { type: 'add', newNo: 119, text: '    assert len(ids) == len(set(ids))' },
  ],
}

/** Verbatim snippet used in the "failure" demo output panel. */
export const mockFailureOutput = `============================= FAILURES ==============================
______ test_resolver_returns_unique_memories ______

seed_pool = <MemoryPool ws_1 entries=37>

    def test_resolver_returns_unique_memories(seed_pool):
        result = resolve_memories("ws_1", "sandbox policy", limit=4)
>       assert len(result) == len({m.id for m in result})
E       assert 4 == 2

tests/memory/test_resolver.py:119: AssertionError
______________________________ summary ______________________________
3 failed, 279 passed, 4 skipped in 12.90s`
