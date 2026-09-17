import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

interface EmptyStateProps {
  icon?: IconName
  title: string
  hint?: string
  actions?: ReactNode
}

export function EmptyState({ icon = 'spark', title, hint, actions }: EmptyStateProps) {
  return (
    <div className="empty">
      <Icon name={icon} size={18} style={{ color: 'var(--g-accent-2)' }} />
      <div className="empty__title">{title}</div>
      {hint ? <div className="empty__hint">{hint}</div> : null}
      {actions ? <div className="empty__actions">{actions}</div> : null}
    </div>
  )
}

/** Definition list row used by the context cards. */
export function KeyValue({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="kv">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}
