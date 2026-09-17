import { useCallback, useEffect, useRef, useState } from 'react'

export interface Point {
  x: number
  y: number
}

interface Size {
  width: number
  height: number
}

interface Options {
  initial: Point
  margin?: number
  getSize: () => Size
  /** Called when a drag ends after actual movement (used to swallow clicks). */
  onDragEnd?: (moved: boolean) => void
}

const DRAG_THRESHOLD = 4

/**
 * Pointer-based drag + viewport clamping for the floating Genos window.
 *
 * Works for the bubble and for both window modes, keeps the window fully on
 * screen when the viewport or the mode changes, and never assumes the window is
 * centred.
 */
export function useDraggable({ initial, margin = 12, getSize, onDragEnd }: Options) {
  const [position, setPosition] = useState<Point>(initial)
  const [dragging, setDragging] = useState(false)
  /** Mirror of `position` so pointer handlers never read a stale closure. */
  const posRef = useRef<Point>(initial)
  const offset = useRef<Point>({ x: 0, y: 0 })
  const active = useRef(false)
  const start = useRef<Point>({ x: 0, y: 0 })
  const moved = useRef(false)

  const applyPosition = useCallback((point: Point) => {
    posRef.current = point
    setPosition(point)
  }, [])

  const clamp = useCallback(
    (point: Point) => {
      const { width, height } = getSize()
      const maxX = Math.max(margin, window.innerWidth - width - margin)
      const maxY = Math.max(margin, window.innerHeight - height - margin)
      return {
        x: Math.min(Math.max(margin, point.x), maxX),
        y: Math.min(Math.max(margin, point.y), maxY),
      }
    },
    [getSize, margin],
  )

  const startDrag = useCallback(
    (event: React.PointerEvent<HTMLElement>) => {
      const handle = event.currentTarget
      const target = event.target as HTMLElement
      if (event.button !== 0) return

      const interactive = target.closest('button, input, textarea, a, [data-no-drag="true"]')
      if (interactive && interactive !== handle) return

      active.current = true
      moved.current = false
      offset.current = {
        x: event.clientX - posRef.current.x,
        y: event.clientY - posRef.current.y,
      }
      start.current = { x: event.clientX, y: event.clientY }
      setDragging(true)
      event.currentTarget.setPointerCapture?.(event.pointerId)
    },
    [],
  )

  useEffect(() => {
    const onPointerMove = (event: PointerEvent) => {
      if (!active.current) return
      const dx = event.clientX - start.current.x
      const dy = event.clientY - start.current.y
      if (!moved.current && Math.hypot(dx, dy) < DRAG_THRESHOLD) return
      moved.current = true
      applyPosition(clamp({ x: event.clientX - offset.current.x, y: event.clientY - offset.current.y }))
    }
    const stop = () => { if (!active.current) return; active.current = false; setDragging(false); onDragEnd?.(moved.current) }
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', stop)
    window.addEventListener('pointercancel', stop)
    return () => { window.removeEventListener('pointermove', onPointerMove); window.removeEventListener('pointerup', stop); window.removeEventListener('pointercancel', stop) }
  }, [clamp, onDragEnd, applyPosition])

  useEffect(() => {
    const reclamp = () => { const next = clamp(posRef.current); if (next.x !== posRef.current.x || next.y !== posRef.current.y) applyPosition(next) }
    reclamp()
    window.addEventListener('resize', reclamp)
    return () => window.removeEventListener('resize', reclamp)
  }, [clamp, applyPosition])

  const move = useCallback((point: Point) => applyPosition(clamp(point)), [clamp, applyPosition])
  const wasDragged = useCallback(() => moved.current, [])
  return { position, dragging, startDrag, move, wasDragged }
}
