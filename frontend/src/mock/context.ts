/**
 * Mock: memories, tasks, goals and action history.
 *
 * DEMO DATA ONLY.
 */
import type { ActionRecord, Goal, MemoryEntry, TaskItem } from '../types'

export const mockMemories: MemoryEntry[] = [
  {
    id: 'mem_1',
    text: 'Resolver uses workspace-scoped memory; never mix scopes across projects.',
    scope: 'project',
    source: 'app/memory/resolver.py',
    at: '2 sessions ago',
  },
  {
    id: 'mem_2',
    text: 'Tests are executed through Python pytest from the repository root.',
    scope: 'project',
    source: 'verification profile',
    at: '4 sessions ago',
  },
  {
    id: 'mem_3',
    text: 'Workflow state persists between sessions and can be resumed by step id.',
    scope: 'workflow',
    source: 'workflow store',
    at: '1 session ago',
  },
  {
    id: 'mem_4',
    text: 'Command execution is restricted to the sandbox allowlist; no network by default.',
    scope: 'project',
    source: 'permissions policy',
    at: '6 sessions ago',
  },
  {
    id: 'mem_5',
    text: 'Rollback restores file state from the pre-edit snapshot, not from Git.',
    scope: 'workflow',
    source: 'safe-write layer',
    at: '3 sessions ago',
  },
]

export const mockTasks: TaskItem[] = [
  { id: 'task_1', title: 'Improve memory resolver', state: 'active', linkedStep: 'step_2' },
  { id: 'task_2', title: 'Add resolver regression tests', state: 'todo' },
  { id: 'task_3', title: 'Harden command sandbox allowlist', state: 'done' },
  { id: 'task_4', title: 'Document workflow resume behaviour', state: 'todo' },
]

export const mockGoal: Goal = {
  id: 'goal_1',
  title: 'Improve project reliability',
  progress: 0.82,
  detail: '3 of 4 tracked tasks resolved · verification green on main',
}

export const mockHistory: ActionRecord[] = [
  { id: 'act_1', kind: 'edit', label: 'Updated resolver.py', detail: 'app/memory/resolver.py · +3 −2', at: '2m ago', status: 'ok' },
  { id: 'act_2', kind: 'test', label: 'Ran test suite', detail: 'pytest -q · 282 passed', at: '4m ago', status: 'ok' },
  { id: 'act_3', kind: 'task', label: 'Created task', detail: 'Add resolver regression tests', at: '6m ago', status: 'ok' },
  { id: 'act_4', kind: 'git', label: 'Inspected Git status', detail: 'main · clean', at: '9m ago', status: 'ok' },
  { id: 'act_5', kind: 'rollback', label: 'Rolled back failed edit', detail: 'app/verification/engine.py', at: 'yesterday', status: 'undone' },
  { id: 'act_6', kind: 'inspect', label: 'Listed project files', detail: '412 files · Python', at: 'yesterday', status: 'ok' },
]
