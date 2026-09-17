import { forwardRef, type CSSProperties, PointerEvent } from 'react'
import { GenosMark } from '../components/ui'
import { STATUS_LABEL, type AgentStatus } from '../types'
import type { Point } from '../hooks/useDraggable'

interface GenosBubbleProps {
  status: AgentStatus
  statusDetail: string
  position: Point
  dragging: boolean
  needsAttention: boolean
  onDragStart: (event: PointerEvent<HTMLButtonElement>) => void
  onOpen: () => void
}

/**
 * Collapsed Genos: a single floating control.
 *
 * State is communicated three ways — ring/glow animation, a badge, and the
 * accessible name — so it never relies on colour alone.
 */
export const GenosBubble = forwardRef<HTMLButtonElement, GenosBubbleProps>(function GenosBubble(
  { status, statusDetail, position, dragging, needsAttention, onDragStart, onOpen },
  ref,
) {
  const style: CSSProperties = { left: position.x, top: position.y }

  return (
    <button
      ref={ref}
      type="button"
      className="bubble"
      data-status={status}
      data-dragging={dragging}
      style={style}
      onPointerDown={onDragStart}
      onClick={onOpen}
      aria-label={`Open Genos. Status: ${STATUS_LABEL[status]}. ${statusDetail}`}
      title={`Genos · ${STATUS_LABEL[status]} — click to open (drag to move)`}
    >
      <span className="bubble__glow" aria-hidden="true" />
      <span className="bubble__ring" aria-hidden="true" />
      <span className="bubble__mark">
        <GenosMark size={22} />
      </span>
      {needsAttention ? (
        <span className="bubble__badge" aria-hidden="true">
          !
        </span>
      ) : null}
    </button>
  )
})
