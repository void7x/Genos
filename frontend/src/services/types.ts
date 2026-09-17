/**
 * SERVICE CONTRACT.
 *
 * This is the only interface the UI is allowed to depend on for data.
 * Components read through `useGenosState()` / `useGenosConnection()` and call
 * methods on the `genosService` singleton — never a concrete implementation.
 * Swapping the mock for the real Genos backend means providing a different
 * implementation of this interface; no component changes.
 *
 * The contract deliberately contains NO demo-only methods (scenario switching,
 * demo reset). Those live in `./demo` and are consumed only by demo UI that
 * renders conditionally when the active service happens to provide them.
 */
import type {
  ActionRecord,
  GenosState,
  GitState,
  Goal,
  MemoryEntry,
  ProjectContext,
  TaskItem,
  TestSummary,
  WorkflowSnapshot,
} from '../types'

/* --------------------------------------------------------------------------
 * Typed result / error model
 *
 * The frontend never invents backend outcomes; it only *communicates* them.
 * Every mutation answers with a `ServiceResult` so the UI can represent
 * success and each failure class without crashing.
 * ------------------------------------------------------------------------ */

export type ServiceErrorCode =
  /** The backend refused the action (its permission system said no). */
  | 'permission-denied'
  /** The request was malformed or not applicable right now. */
  | 'invalid-request'
  /** The backend cannot be reached at all. */
  | 'backend-unavailable'
  /** The backend state moved on (stale UI, action already handled, busy). */
  | 'conflict'
  /** The backend did not answer in time. */
  | 'timeout'
  /** Anything the frontend cannot classify. */
  | 'unknown'

export interface ServiceError {
  code: ServiceErrorCode
  message: string
}

export type ServiceResult<T = void> =
  | { ok: true; value: T }
  | { ok: false; error: ServiceError }

export const ok = <T,>(value: T): ServiceResult<T> => ({ ok: true, value })
export const okVoid = (): ServiceResult<void> => ({ ok: true, value: undefined })
export const fail = (code: ServiceErrorCode, message: string): ServiceResult<never> => ({
  ok: false,
  error: { code, message },
})

/* --------------------------------------------------------------------------
 * Connection lifecycle
 *
 * The transport needs an asynchronous initialization (subscribe + initial
 * snapshot). The UI gates on this state instead of ever observing a throw.
 * ------------------------------------------------------------------------ */

export type ConnectionState =
  | { status: 'idle' }
  | { status: 'connecting' }
  | { status: 'ready' }
  | { status: 'error'; error: ServiceError }

/* --------------------------------------------------------------------------
 * The contract
 * ------------------------------------------------------------------------ */

export interface GenosService {
  /* ----------------------------------------------------------- lifecycle */

  /**
   * Start (or retry) the transport initialization: subscribe to pushes, fetch
   * the initial snapshot, then flip the connection to `ready` or `error`.
   * Idempotent — safe to call from a React effect and from a Retry button.
   */
  init(): Promise<ServiceResult<void>>

  /** Current connection state; changes are announced through `subscribe`. */
  getConnectionState(): ConnectionState

  /* ---------------------------------------------------------- store API */

  /** Subscribe to state/connection changes. Returns an unsubscribe function. */
  subscribe(listener: () => void): () => void

  /**
   * Current aggregate snapshot. Referentially stable between emits.
   * Only meaningful once the connection is `ready` — the UI gates on that.
   */
  getState(): GenosState

  /* ------------------------------------------------------------- reads */

  getProject(): Promise<ProjectContext>
  getGitStatus(): Promise<GitState>
  getTestSummary(): Promise<TestSummary>
  getTasks(): Promise<TaskItem[]>
  getGoal(): Promise<Goal>
  getMemories(): Promise<MemoryEntry[]>
  getWorkflow(): Promise<WorkflowSnapshot>
  getActionHistory(): Promise<ActionRecord[]>

  /* ------------------------------------------------------------ writes */

  /** Send a developer instruction to Genos. */
  sendMessage(text: string): Promise<ServiceResult<void>>
  /** Approve the currently pending permission request. */
  approveAction(): Promise<ServiceResult<void>>
  /** Deny the currently pending permission request. */
  denyAction(): Promise<ServiceResult<void>>
  /** Continue an interrupted workflow from its persisted state. */
  resumeWorkflow(): Promise<ServiceResult<void>>
  /** Re-run a failed workflow from the start (retry semantics). */
  retryWorkflow(): Promise<ServiceResult<void>>
  /** Ask Genos to roll the last unverified change back. */
  requestRollback(): Promise<ServiceResult<void>>

  /* ------------------------------------------------------- notifications */

  /** Local housekeeping: stop showing a notification. */
  dismissNotification(id: string): void
}
