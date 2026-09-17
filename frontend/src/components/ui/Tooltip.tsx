import { useId, type ReactNode } from 'react'

interface TooltipProps {
  label: string
  children: ReactNode
}

/**
 * Accessible tooltip: visible on hover *and* keyboard focus, and exposed to
 * assistive tech through aria-describedby.
 */
export function Tooltip({ label, children }: TooltipProps) {
  const id = useId()
  return (
    <span className="tip" aria-describedby={id}>
      {children}
      <span className="tip__bubble" role="tooltip" id={id}>
        {label}
      </span>
    </span>
  )
}
