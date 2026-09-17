/**
 * Transport adapter lifecycle + typed command contract.
 */
import { describe, expect, it } from 'vitest'
import {
  createHttpBackedService,
  GenosTransportError,
  type GenosCommand,
  type GenosTransport,
} from '../services/transport'
import type { GenosState } from '../types'
import { mockProject } from '../mock/project'
import { mockGoal, mockHistory, mockMemories, mockTasks } from '../mock/context'
import { createEmptyWorkflow } from '../mock/workflow'

const makeState = (detail: string): GenosState => ({
  project: mockProject,
  status: 'idle',
  statusDetail: detail,
  messages: [],
  workflow: createEmptyWorkflow(),
  permission: null,
  verification: null,
  recovery: null,
  rollback: null,
  memories: mockMemories,
  tasks: mockTasks,
  goal: mockGoal,
  history: mockHistory,
  files: [],
  notifications: [],
  busy: false,
})

interface FakeTransport extends GenosTransport {
  commands: GenosCommand[]
  push: (state: GenosState) => void
  resolveFetch: (state: GenosState) => void
  rejectFetch: (cause: unknown) => void
}

function makeTransport(fetchMode: 'manual' | 'fail' = 'manual'): FakeTransport {
  let listener: ((s: GenosState) => void) | null = null
  let fetchSettlers: {
    resolve: (s: GenosState) => void
    reject: (e: unknown) => void
  } | null = null
  let preResolved: GenosState | null = null
  let preRejected: unknown = null

  const fake: FakeTransport = {
    commands: [],
    push: (state) => listener?.(state),
    resolveFetch: (state) => {
      if (fetchSettlers) fetchSettlers.resolve(state)
      else preResolved = state
    },
    rejectFetch: (cause) => {
      if (fetchSettlers) fetchSettlers.reject(cause)
      else preRejected = cause
    },
    fetchState: () => {
      if (fetchMode === 'fail') return Promise.reject(new TypeError('network down'))
      if (preResolved) return Promise.resolve(preResolved)
      if (preRejected) return Promise.reject(preRejected)
      return new Promise<GenosState>((resolve, reject) => {
        fetchSettlers = { resolve, reject }
      })
    },
    onState: (l) => {
      listener = l
      return () => {
        listener = null
      }
    },
    command: async (command) => {
      fake.commands.push(command)
    },
  }
  return fake
}

const flush = () => new Promise((r) => setTimeout(r, 0))

describe('transport initialization', () => {
  it('connects: subscribe → fetch → ready, snapshot available', async () => {
    const transport = makeTransport()
    const service = createHttpBackedService(transport)
    expect(service.getConnectionState().status).toBe('idle')

    const init = service.init()
    expect(service.getConnectionState().status).toBe('connecting')

    transport.resolveFetch(makeState('from-fetch'))
    const result = await init
    expect(result.ok).toBe(true)
    expect(service.getConnectionState().status).toBe('ready')
    expect(service.getState().statusDetail).toBe('from-fetch')
    // referentially stable between emits
    expect(service.getState()).toBe(service.getState())
  })

  it('keeps pushes that arrive while the initial fetch is in flight', async () => {
    const transport = makeTransport()
    const service = createHttpBackedService(transport)
    const init = service.init()

    transport.push(makeState('from-push'))
    await flush()
    // the push proves connectivity: ready even though fetch is still pending
    expect(service.getConnectionState().status).toBe('ready')
    expect(service.getState().statusDetail).toBe('from-push')

    // a late fetch result must not overwrite the newer push
    transport.resolveFetch(makeState('stale-fetch'))
    await init
    expect(service.getState().statusDetail).toBe('from-push')
  })

  it('surfaces fetch failure as a typed error and recovers on retry', async () => {
    const failing = makeTransport('fail')
    const service = createHttpBackedService(failing)
    const result = await service.init()

    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('backend-unavailable')
    }
    expect(service.getConnectionState().status).toBe('error')

    // retry with a working transport behind the same adapter instance is not
    // possible (transport is fixed) — but init is retryable in principle;
    // simulate the UI's Retry by rebuilding the adapter with a good transport.
    const good = makeTransport()
    const service2 = createHttpBackedService(good)
    good.resolveFetch(makeState('recovered'))
    const second = await service2.init()
    expect(second.ok).toBe(true)
    expect(service2.getConnectionState().status).toBe('ready')
  })

  it('commands are refused while not connected', async () => {
    const transport = makeTransport()
    const service = createHttpBackedService(transport)
    const result = await service.sendMessage('hello')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('backend-unavailable')
    expect(transport.commands).toHaveLength(0)
  })
})

describe('typed command contract', () => {
  it('maps service calls onto the closed GenosCommand union', async () => {
    const transport = makeTransport()
    const service = createHttpBackedService(transport)
    transport.resolveFetch(makeState('ready'))
    await service.init()

    await service.sendMessage('fix tests')
    await service.approveAction()
    await service.denyAction()
    await service.resumeWorkflow()
    await service.retryWorkflow()
    await service.requestRollback()
    service.dismissNotification('n1')
    await flush()

    expect(transport.commands).toEqual([
      { type: 'sendMessage', text: 'fix tests' },
      { type: 'approveAction' },
      { type: 'denyAction' },
      { type: 'resumeWorkflow' },
      { type: 'retryWorkflow' },
      { type: 'requestRollback' },
      { type: 'dismissNotification', id: 'n1' },
    ])
  })

  it('propagates typed transport errors as ServiceResult', async () => {
    const transport = makeTransport()
    transport.command = async () => {
      throw new GenosTransportError('permission-denied', 'backend said no')
    }
    const service = createHttpBackedService(transport)
    transport.resolveFetch(makeState('ready'))
    await service.init()

    const result = await service.approveAction()
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.code).toBe('permission-denied')
      expect(result.error.message).toBe('backend said no')
    }
  })

  it('maps timeouts to the timeout error code', async () => {
    const transport = makeTransport()
    transport.command = async () => {
      throw Object.assign(new Error('request timed out'), { name: 'TimeoutError' })
    }
    const service = createHttpBackedService(transport)
    transport.resolveFetch(makeState('ready'))
    await service.init()

    const result = await service.denyAction()
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('timeout')
  })
})
