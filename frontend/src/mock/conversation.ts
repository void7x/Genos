/**
 * Mock: conversation seed content + the scripted Genos replies used by the demo.
 *
 * DEMO DATA ONLY — these strings are pre-written, nothing is generated.
 */
import type { ChatMessage, MessageBlock } from '../types'
import { mockFailureOutput, mockResolverSnippet } from './files'

const now = () => new Date().toISOString()

let seq = 0
export const nextId = (prefix: string) => `${prefix}_${++seq}_${Date.now().toString(36)}`

export function userMessage(text: string): ChatMessage {
  return { id: nextId('msg'), role: 'user', blocks: [{ kind: 'text', text }], at: now() }
}

export function genosMessage(blocks: MessageBlock[], note?: string): ChatMessage {
  return { id: nextId('msg'), role: 'genos', blocks, note, at: now() }
}

/** Opening state: no conversation yet, idle empty state. */
export const emptyConversation: ChatMessage[] = []

/**
 * Seed conversation shown by the "resume session" demo so the expanded
 * workspace is not empty on first paint.
 */
export function seedConversation(): ChatMessage[] {
  return [
    userMessage('Why is the memory resolver returning duplicate results?'),
    genosMessage([
      {
        kind: 'text',
        text: 'I inspected the project and found 3 related files. The duplicate entries come from `_candidate_pool` returning the same memory under two scopes, and `resolve_memories` ranks before de-duplicating.',
      },
      {
        kind: 'fileList',
        files: [
          { path: 'app/memory/resolver.py', line: 74, change: 'original' },
          { path: 'app/memory/manager.py', change: 'original' },
          { path: 'tests/memory/test_resolver.py', line: 118, change: 'original' },
        ],
      },
      { kind: 'code', language: 'python', filename: 'app/memory/resolver.py', code: mockResolverSnippet },
      {
        kind: 'details',
        summary: 'Diagnostics · 2 findings',
        body: [
          {
            kind: 'text',
            text: 'ruff: no findings. Static check flags `ranked` as a list of tuples where the second element can repeat — `sorted(zip(...), reverse=True)` keeps both copies.',
          },
        ],
      },
    ]),
    userMessage('Show me what changed.'),
    genosMessage([
      {
        kind: 'text',
        text: 'Nothing has been written yet — the working tree is clean on `main`. Here is the change I have prepared for your approval.',
      },
      { kind: 'command', command: 'git status --porcelain', output: '(no output · working tree clean)' },
    ]),
  ]
}

/** Scripted Genos replies for the demo workflow. */
export const script = {
  understanding: () =>
    genosMessage(
      [{ kind: 'text', text: 'Understanding request. Reading workspace context before I touch anything.' }],
      'Understanding request…',
    ),
  context: () =>
    genosMessage([
      {
        kind: 'text',
        text: 'Workspace `Genos` · Python · branch `main` · working tree clean. 282 tests passed on the last verification run.',
      },
      { kind: 'command', command: 'pytest -q --collect-only | tail -1', output: '286 tests collected in 0.42s' },
    ]),
  plan: () =>
    genosMessage(
      [
        {
          kind: 'text',
          text: "I've prepared a 4-step plan. Step 2 writes to the project, so I will ask for your approval before it runs.",
        },
      ],
      'Plan ready · awaiting approval',
    ),
  approved: () =>
    genosMessage(
      [{ kind: 'text', text: 'Approval recorded. Applying the change under a pre-edit snapshot so it can be rolled back.' }],
      'Executing plan',
    ),
  success: () =>
    genosMessage([
      {
        kind: 'text',
        text: 'Verification passed. The resolver now de-duplicates before ranking and the full suite is green.',
      },
      { kind: 'command', command: 'pytest -q', output: '282 passed, 4 skipped in 12.40s' },
    ]),
  failed: () =>
    genosMessage(
      [
        { kind: 'text', text: 'The test suite failed after the change. 3 tests failed in `tests/memory`.' },
        { kind: 'code', language: 'text', code: mockFailureOutput },
      ],
      'Verification failed',
    ),
  rolledBack: () =>
    genosMessage(
      [{ kind: 'text', text: 'I restored the previous file state. `app/memory/resolver.py` is back to the committed version.' }],
      'Rolled back',
    ),
  denied: () =>
    genosMessage(
      [{ kind: 'text', text: 'Understood — no changes were made. The plan stays paused at step 2 and can be resumed later.' }],
      'Denied',
    ),
}
