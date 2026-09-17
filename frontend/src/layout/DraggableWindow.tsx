import type { CSSProperties, PointerEvent, ReactNode } from 'react'
import type { Point } from '../hooks/useDraggable'

export type WindowMode = 'compact' | 'expanded'

interface DraggableWindowProps {
  mode: WindowMode
  position: Point
  dragging: boolean
  onDragStart: (event: PointerEvent<HTMLElement>) => void
  titleBar: ReactNode
  children: ReactNode
  labelledBy?: string
}

/**
 * The floating Genos window.
 *
 * Position is owned by the shell so the bubble and the window share an anchor
 * point; the window itself only renders at that point and forwards drag starts
 * from its title bar.
 */
export function DraggableWindow({
  mode,
  position,
  dragging,
  onDragStart,
  titleBar,
  children,
  labelledBy,
}: DraggableWindowProps) {
  const style: CSSProperties = {
    left: position.x,
    top: position.y,
  }

  return (
    <div
      className="window"
      data-mode={mode}
      data-dragging={dragging}
      style={style}
      role="dialog"
      aria-modal={false}
      aria-label="Genos assistant"
      aria-labelledby={labelledBy}
    >
      <div className="titlebar" data-dragging={dragging} onPointerDown={onDragStart}>
        {titleBar}
      </div>
      {children}
    </div>
  )
}
