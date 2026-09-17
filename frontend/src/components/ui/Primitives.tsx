import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'
import type { AgentStatus } from '../../types'

/* ------------------------------------------------------------- status dot */

export function StatusDot({ status, label }: { status: AgentStatus; label?: string }) {
  return (
    <span
      className="dot"
      data-status={status}
      role="img"
      aria-label={label ?? `Status: ${status}`}
    />
  )
}

/* ------------------------------------------------------------------ chips */

type ChipTone = 'default' | 'accent' | 'ok' | 'warn' | 'err'

const CHIP_TONE: Record<ChipTone, string> = {
  default: '',
  accent: 'chip--accent',
  ok: 'chip--ok',
  warn: 'chip--warn',
  err: 'chip--err',
}

interface ChipProps {
  icon?: IconName
  tone?: ChipTone
  mono?: boolean
  title?: string
  children: ReactNode
}

export function Chip({ icon, tone = 'default', mono, title, children }: ChipProps) {
  return (
    <span
      className={['chip', CHIP_TONE[tone], mono ? 'chip--mono' : ''].filter(Boolean).join(' ')}
      title={title}
    >
      {icon ? <Icon name={icon} size={11} /> : null}
      <span>{children}</span>
    </span>
  )
}

/* --------------------------------------------------------------- progress */

export function ProgressBar({
  value,
  tone = 'accent',
  size = 'sm',
  label,
}: {
  value: number
  tone?: 'accent' | 'ok' | 'err'
  size?: 'sm' | 'lg'
  label?: string
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  return (
    <div
      className={['progress', size === 'lg' ? 'progress--lg' : ''].filter(Boolean).join(' ')}
      data-tone={tone === 'accent' ? undefined : tone}
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label ?? 'Progress'}
    >
      <div className="progress__fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

/* ------------------------------------------------------------- thinking */

export function ThinkingDots({ label = 'Working' }: { label?: string }) {
  return (
    <span className="thinking-dots" role="status" aria-label={label}>
      <i />
      <i />
      <i />
    </span>
  )
}
