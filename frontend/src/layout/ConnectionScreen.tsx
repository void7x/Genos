import { Button, GenosMark, Icon } from '../components/ui'
import type { ServiceError } from '../services/types'

/**
 * Lifecycle surfaces for the transport connection.
 *
 * The data UI never mounts before `ready`, so a slow or failing backend
 * produces a calm loading/error state instead of a crash.
 */
export function ConnectionScreen({
  state,
  error,
  onRetry,
}: {
  state: 'connecting' | 'error'
  error?: ServiceError
  onRetry: () => void
}) {
  return (
    <div className="desktop" role="status">
      <div className="desktop__grid" aria-hidden="true" />
      <div
        className="connection-screen"
        role={state === 'error' ? 'alertdialog' : undefined}
        aria-label={state === 'error' ? 'Genos cannot connect' : 'Connecting to Genos'}
      >
        <GenosMark size={26} />
        <div className="connection-screen__title">
          {state === 'error' ? 'Genos is unreachable' : 'Connecting to Genos…'}
        </div>

        {state === 'error' && error ? (
          <>
            <div className="connection-screen__detail" data-tone={error.code}>
              <Icon name="alert" size={13} />
              <span>
                <strong>{error.code}</strong> — {error.message}
              </span>
            </div>
            <p className="connection-screen__hint">
              The backend stays authoritative for everything; the UI will not guess state.
            </p>
            <Button variant="primary" icon="refresh" onClick={onRetry}>
              Retry connection
            </Button>
          </>
        ) : (
          <div className="connection-screen__detail" data-tone="info">
            <span className="thinking-dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span>Waiting for the first state snapshot…</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Transient, dismissible notice for failed service calls (typed errors from
 * the integration contract). Rendered near the floating window, announced to
 * assistive tech, and never fatal to the app.
 */
export function ActionErrorToast({
  error,
  onDismiss,
  anchor,
}: {
  error: ServiceError
  onDismiss: () => void
  anchor: { left: number; top: number }
}) {
  return (
    <div className="toasts" style={{ left: anchor.left, top: anchor.top }}>
      <div className="toast" data-tone="error" role="alert">
        <span className="toast__icon">
          <Icon name="alert" size={14} />
        </span>
        <div>
          <div className="toast__title">Action failed · {error.code}</div>
          <div className="toast__body">{error.message}</div>
        </div>
        <button
          type="button"
          className="win-btn"
          style={{ justifySelf: 'end' }}
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          <Icon name="close" size={12} />
        </button>
      </div>
    </div>
  )
}
