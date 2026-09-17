import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

type CardTone = 'default' | 'accent' | 'warn' | 'ok' | 'err'

interface CardProps {
  title?: string
  icon?: IconName
  tone?: CardTone
  actions?: ReactNode
  flush?: boolean
  children: ReactNode
  /** Announce content changes politely — used for status cards. */
  live?: 'polite' | 'assertive'
  id?: string
}

/** Section container used across every rail and the compact panel. */
export function Card({
  title,
  icon,
  tone = 'default',
  actions,
  flush,
  children,
  live,
  id,
}: CardProps) {
  return (
    <section className="card" data-tone={tone === 'default' ? undefined : tone} aria-live={live} id={id}>
      {title ? (
        <header className="card__head">
          {icon ? <Icon name={icon} size={12} style={{ color: 'var(--g-text-4)' }} /> : null}
          <h3>{title}</h3>
          {actions ? <div className="card__head-right">{actions}</div> : null}
        </header>
      ) : null}
      <div className={['card__body', flush ? 'card__body--flush' : ''].filter(Boolean).join(' ')}>
        {children}
      </div>
    </section>
  )
}
