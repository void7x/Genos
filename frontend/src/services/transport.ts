/**
 * TRANSPORT LAYER — the single seam between this UI and the Genos backend.
 *
 * NOTHING HERE IS WIRED UP. The prototype always runs `MockGenosService`
 * (see `src/services/genosService.ts`). This file exists so that integration
 * is a mechanical job rather than a redesign:
 *
 *   1. Implement `GenosTransport` against the real Genos backend
 *      (HTTP, WebSocket, IPC — whatever the desktop shell exposes).
 *   2. Pass it to `createHttpBackedService`.
 *   3. Point `genosService.ts` at the result instead of the mock.
 *
 * The UI never learns which implementation it is talking to.
 *
 * SECURITY BOUNDARY
 * -----------------
 * The transport only ever sends members of the closed `GenosCommand` union —
 * the frontend can *request* known Genos operations, it can never name an
 * arbitrary backend command, and it can never ask the backend to run a shell
 * string. The Python backend stays the only authority for permission checks,
 * filesystem access, command execution, Git operations, verification,
 * rollback and workflow state. Payloads are plain data; the backend validates
 * everything again.
 */
import {
  fail,
  okVoid,
  type ConnectionState,
  type GenosService,
  type ServiceError,
  type ServiceErrorCode,
  type ServiceResult,
} from './types'
import type { GenosState } from '../types'

export type GenosCommand =
  | { type: 'sendMessage'; text: string }
  | { type: 'approveAction' }
  | { type: 'denyAction' }
  | { type: 'resumeWorkflow' }
  | { type: 'retryWorkflow' }
  | { type: 'requestRollback' }
  | { type: 'dismissNotification'; id: string }

export class GenosTransportError extends Error {
  constructor(
    readonly code: ServiceErrorCode,
    message: string,
  ) {
    super(message)
    this.name = 'GenosTransportError'
  }
}

export interface GenosTransport {
  fetchState(): Promise<GenosState>
  onState(listener: (state: GenosState) => void): () => void
  command(command: GenosCommand): Promise<void>
}

export function mapTransportError(cause: unknown): ServiceError {
  if (cause instanceof GenosTransportError) {
    return { code: cause.code, message: cause.message }
  }
  const name = cause instanceof Error ? cause.name : ''
  const message = cause instanceof Error ? cause.message : String(cause)
  if (name === 'TimeoutError' || name === 'AbortError' || /timeout/i.test(message)) {
    return { code: 'timeout', message: 'The Genos backend did not answer in time.' }
  }
  if (typeof cause === 'object' && cause !== null && 'code' in cause) {
    const code = (cause as { code: unknown }).code
    const known: readonly string[] = [
      'permission-denied',
      'invalid-request',
      'backend-unavailable',
      'conflict',
      'timeout',
      'unknown',
    ]
    if (typeof code === 'string' && known.includes(code)) {
      return { code: code as ServiceErrorCode, message }
    }
  }
  return { code: 'backend-unavailable', message: 'The Genos backend cannot be reached.' }
}

export function createHttpBackedService(transport: GenosTransport): GenosService {
  let snapshot: GenosState | null = null
  let connection: ConnectionState = { status: 'idle' }
  let initPromise: Promise<ServiceResult<void>> | null = null
  const listeners = new Set<() => void>()

  const emit = () => listeners.forEach((l) => l())

  const setConnection = (next: ConnectionState) => {
    connection = next
    emit()
  }

  transport.onState((next) => {
    snapshot = next
    if (connection.status === 'connecting') setConnection({ status: 'ready' })
    else emit()
  })

  const init = (): Promise<ServiceResult<void>> => {
    if (connection.status === 'connecting' && initPromise) return initPromise
    if (connection.status === 'ready') return Promise.resolve(okVoid())

    setConnection({ status: 'connecting' })

    initPromise = transport
      .fetchState()
      .then((initial) => {
        if (snapshot === null) snapshot = initial
        setConnection({ status: 'ready' })
        return okVoid()
      })
      .catch((cause) => {
        if (snapshot !== null) {
          setConnection({ status: 'ready' })
          return okVoid()
        }
        const error = mapTransportError(cause)
        setConnection({ status: 'error', error })
        return { ok: false, error } as ServiceResult<void>
      })

    return initPromise
  }

  const requireSnapshot = (): GenosState => {
    if (!snapshot) {
      throw new Error('GenosTransport: snapshot requested before the connection is ready')
    }
    return snapshot
  }

  const run = async (command: GenosCommand): Promise<ServiceResult<void>> => {
    if (connection.status !== 'ready') {
      return fail('backend-unavailable', 'Genos is not connected yet.')
    }
    try {
      await transport.command(command)
      return okVoid()
    } catch (cause) {
      return { ok: false, error: mapTransportError(cause) }
    }
  }

  return {
    init,
    getConnectionState: () => connection,
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    getState: () => requireSnapshot(),
    getProject: async () => requireSnapshot().project,
    getGitStatus: async () => requireSnapshot().project.gitState,
    getTestSummary: async () => requireSnapshot().project.tests,
    getTasks: async () => requireSnapshot().tasks,
    getGoal: async () => requireSnapshot().goal,
    getMemories: async () => requireSnapshot().memories,
    getWorkflow: async () => requireSnapshot().workflow,
    getActionHistory: async () => requireSnapshot().history,
    sendMessage: (text) => run({ type: 'sendMessage', text }),
    approveAction: () => run({ type: 'approveAction' }),
    denyAction: () => run({ type: 'denyAction' }),
    resumeWorkflow: () => run({ type: 'resumeWorkflow' }),
    retryWorkflow: () => run({ type: 'retryWorkflow' }),
    requestRollback: () => run({ type: 'requestRollback' }),
    dismissNotification: (id) => {
      void run({ type: 'dismissNotification', id })
    },
  }
}
