/**
 * Contract-level semantics of the mock service + demo isolation.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { genosService } from '../services/genosService'
import { getDemoControls, type DemoControls } from '../services/demo'
import type { GenosService } from '../services/types'

const FIX = 'Fix the failing tests in the memory resolver.'

describe('demo controls are isolated from the production contract', () => {
  it('the singleton is a plain GenosService at the type level', () => {
    const service: GenosService = genosService
    expect(typeof service.resumeWorkflow).toBe('function')
    expect(typeof service.retryWorkflow).toBe('function')
  })

  it('getDemoControls finds them on the mock…', () => {
    const demo: DemoControls | null = getDemoControls(genosService)
    expect(demo).not.toBeNull()
    expect(['success', 'failure']).toContain(demo!.getDemoScenario())
  })

  it('…and returns null for a production-shaped service', () => {
    const production: GenosService = {
      init: async () => ({ ok: true, value: undefined }),
      getConnectionState: () => ({ status: 'ready' }),
      subscribe: () => () => undefined,
      getState: () => {
        throw new Error('unused')
      },
      getProject: async () => {
        throw new Error('unused')
      },
      getGitStatus: async () => {
        throw new Error('unused')
      },
      getTestSummary: async () => {
        throw new Error('unused')
      },
      getTasks: async () => {
        throw new Error('unused')
      },
      getGoal: async () => {
        throw new Error('unused')
      },
      getMemories: async () => {
        throw new Error('unused')
      },
      getWorkflow: async () => {
        throw new Error('unused')
      },
      getActionHistory: async () => {
        throw new Error('unused')
      },
      sendMessage: async () => ({ ok: true, value: undefined }),
      approveAction: async () => ({ ok: true, value: undefined }),
      denyAction: async () => ({ ok: true, value: undefined }),
      resumeWorkflow: async () => ({ ok: true, value: undefined }),
      retryWorkflow: async () => ({ ok: true, value: undefined }),
      requestRollback: async () => ({ ok: true, value: undefined }),
      dismissNotification: () => undefined,
    }
    expect(getDemoControls(production)).toBeNull()
  })
})

describe('resume vs retry semantics', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
    getDemoControls(genosService)?.reset()
  })

  const advance = (ms: number) => vi.advanceTimersByTimeAsync(ms)

  it('resume without an interrupted workflow is a typed conflict', async () => {
    const result = await genosService.resumeWorkflow()
    expect(result).toMatchObject({ ok: false, error: { code: 'conflict' } })
  })

  it('retry without any workflow is a typed invalid-request', async () => {
    const result = await genosService.retryWorkflow()
    expect(result).toMatchObject({ ok: false, error: { code: 'invalid-request' } })
  })

  it('deny ⇒ interrupted ⇒ resume continues (not restarts)', async () => {
    await genosService.sendMessage(FIX)
    await advance(3000) // understanding → context → plan → permission

    const denied = await genosService.denyAction()
    expect(denied.ok).toBe(true)
    expect(genosService.getState().workflow.interrupted).toBe(true)

    const messagesBefore = genosService.getState().messages.length
    const resumed = await genosService.resumeWorkflow()
    expect(resumed.ok).toBe(true)
    expect(genosService.getState().workflow.interrupted).toBe(false)

    await advance(1200) // resume re-issues the approval gate
    const permission = genosService.getState().permission
    expect(permission?.state).toBe('pending')

    // resume continued: the conversation grew, it did not reset to the seed
    expect(genosService.getState().messages.length).toBeGreaterThan(messagesBefore)
    expect(genosService.getState().workflow.steps).toHaveLength(4)
  })

  it('validation guards: empty send, double approve, rollback without failure', async () => {
    expect(await genosService.sendMessage('   ')).toMatchObject({
      ok: false,
      error: { code: 'invalid-request' },
    })
    expect(await genosService.approveAction()).toMatchObject({
      ok: false,
      error: { code: 'conflict' },
    })
    expect(await genosService.requestRollback()).toMatchObject({
      ok: false,
      error: { code: 'conflict' },
    })
  })

  it('sending while busy is a typed conflict', async () => {
    await genosService.sendMessage(FIX)
    await advance(500)
    const second = await genosService.sendMessage('another task')
    expect(second).toMatchObject({ ok: false, error: { code: 'conflict' } })
  })
})
