import { useState, type ReactNode } from 'react'
import { Icon } from './Icon'

interface DetailsProps {
  summary: ReactNode
  icon?: 'chevron'
  defaultOpen?: boolean
  children: ReactNode
  /** Extra class on the summary row. */
  className?: string
}

/** Expandable technical detail — used for diagnostics, memories and failures. */
export function Details({ summary, defaultOpen = false, children, className = '' }: DetailsProps) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className={['details', className].filter(Boolean).join(' ')} data-open={open}>
      <button
        type="button"
        className="details__summary"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Icon name="chevron" size={12} className="icon icon--chevron" />
        <span>{summary}</span>
      </button>
      {open ? <div className="details__content">{children}</div> : null}
    </div>
  )
}
