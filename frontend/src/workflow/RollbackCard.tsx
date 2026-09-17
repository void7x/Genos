import { Card, Icon } from '../components/ui'
import type { RollbackState } from '../types'

/** Rollback evidence: what was restored, and confirmation that it landed. */
export function RollbackCard({ rollback }: { rollback: RollbackState }) {
  return (
    <Card title="Rollback" icon="undo" tone="warn" live="polite">
      <p className="notice__detail" style={{ marginTop: 0 }}>
        {rollback.detail}
      </p>
      <div className="permission__file">
        <Icon name="file" size={12} style={{ color: 'var(--g-text-4)' }} />
        <span>{rollback.target}</span>
      </div>
      <div
        className="permission__resolved"
        style={{ color: rollback.restored ? 'var(--g-ok)' : 'var(--g-warn)' }}
      >
        <Icon name={rollback.restored ? 'check' : 'clock'} size={12} />
        {rollback.restored ? 'Original state restored' : 'Restore in progress…'}
      </div>
    </Card>
  )
}
