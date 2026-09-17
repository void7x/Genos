import { Button, Card, Icon, ThinkingDots } from '../components/ui'
import type { RecoveryState } from '../types'

interface RecoveryCardProps {
  recovery: RecoveryState
  onInspect?: () => void
  onRollback?: () => void
}

/** Recovery states: automatic retry, or "this needs a human". */
export function RecoveryCard({ recovery, onInspect, onRollback }: RecoveryCardProps) {
  return (
    <Card
      title="Recovery"
      icon="refresh"
      tone={recovery.automatic ? 'warn' : 'err'}
      live="assertive"
    >
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
        <span style={{ paddingTop: 2, color: recovery.automatic ? 'var(--g-warn)' : 'var(--g-err)' }}>
          <Icon name={recovery.automatic ? 'spinner' : 'alert'} size={14} />
        </span>
        <div style={{ minWidth: 0 }}>
          <div className="notice__title">{recovery.title}</div>
          <p className="notice__detail" style={{ marginTop: 3 }}>
            {recovery.detail}
          </p>
          <div className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-label)', marginTop: 4 }}>
            {recovery.automatic ? (
              <>
                <ThinkingDots label="Retrying" /> attempt {recovery.attempt} ·{' '}
                {recovery.attempt === 1 ? 'retrying test command…' : 're-running verification…'}
              </>
            ) : (
              <>automatic recovery exhausted · {recovery.attempt} attempts</>
            )}
          </div>

          <div className="notice__actions">
            {onInspect ? (
              <Button size="sm" icon="eye" onClick={onInspect}>
                Inspect failure
              </Button>
            ) : null}
            {onRollback && !recovery.automatic ? (
              <Button size="sm" variant="danger" icon="undo" onClick={onRollback}>
                Roll back change
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </Card>
  )
}
