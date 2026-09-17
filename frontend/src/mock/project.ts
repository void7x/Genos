/**
 * Mock: project, git and test context.
 *
 * DEMO DATA ONLY. Nothing here executes; these are static descriptions used to
 * render the prototype. Replace with a real backend call in
 * `src/services/backendService.ts` (see `getProject`).
 */
import type { ProjectContext, TestSummary } from '../types'

export const mockProject: ProjectContext = {
  id: 'prj_genos',
  name: 'Genos',
  path: '~/src/genos',
  language: 'Python',
  branch: 'main',
  workspace: 'genos · local workspace',
  gitState: {
    branch: 'main',
    clean: true,
    modifiedFiles: 0,
    ahead: 0,
    behind: 0,
    lastCommit: 'a41f9c2 · harden command sandbox allowlist',
  },
  tests: {
    passed: 282,
    failed: 0,
    skipped: 4,
    durationMs: 12_400,
    lastRun: '14m ago',
  },
}

/** Failing-test variant used by the failure / rollback demo scenarios. */
export const mockFailingTests: TestSummary = {
  passed: 279,
  failed: 3,
  skipped: 4,
  durationMs: 12_900,
  lastRun: 'just now',
}

export const mockProjectTree = [
  { path: 'app/agent/multi_step.py', change: 'original' as const },
  { path: 'app/chat/runtime.py', change: 'original' as const },
  { path: 'app/memory/manager.py', change: 'original' as const },
  { path: 'app/memory/resolver.py', change: 'modified' as const, line: 74 },
  { path: 'app/verification/engine.py', change: 'original' as const },
  { path: 'tests/memory/test_resolver.py', change: 'original' as const, line: 118 },
  { path: 'tests/verification/test_engine.py', change: 'original' as const },
]
