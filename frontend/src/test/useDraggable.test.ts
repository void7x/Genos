/**
 * Drag behaviour: clamping, mode-change re-clamping, and click-vs-drag.
 */
import { act, renderHook } from '@testing-library/react'
import type { PointerEvent as ReactPointerEvent } from 'react'
import { describe, expect, it } from 'vitest'
import { useDraggable } from '../hooks/useDraggable'

interface DragHook {
  result: {
    current: {
      startDrag: (event: ReactPointerEvent<HTMLElement>) => void
      position: { x: number; y: number }
      wasDragged: () => boolean
    }
  }
}

const fire = (type: string, x: number, y: number) => {
  act(() => {
    window.dispatchEvent(new MouseEvent(type, { clientX: x, clientY: y, bubbles: true }))
  })
}

const startAt = (hook: DragHook, x: number, y: number) => {
  const el = document.createElement('div')
  act(() => {
    hook.result.current.startDrag({
      button: 0,
      clientX: x,
      clientY: y,
      pointerId: 1,
      target: el,
      currentTarget: el,
    } as unknown as ReactPointerEvent<HTMLElement>)
  })
}

describe('useDraggable', () => {
  it('drags and clamps to the viewport', () => {
    const hook = renderHook(() =>
      useDraggable({ initial: { x: 100, y: 100 }, getSize: () => ({ width: 200, height: 200 }) }),
    )

    startAt(hook, 110, 110)
    fire('pointermove', 300, 300)
    fire('pointerup', 300, 300)
    expect(hook.result.current.position).toEqual({ x: 290, y: 290 })

    // dragging far beyond the bottom-right corner clamps inside the viewport
    startAt(hook, 300, 300)
    fire('pointermove', 5000, 5000)
    fire('pointerup', 5000, 5000)
    expect(hook.result.current.position).toEqual({
      x: window.innerWidth - 200 - 12,
      y: window.innerHeight - 200 - 12,
    })

    // …and beyond the top-left corner
    startAt(hook, window.innerWidth - 200, window.innerHeight - 200)
    fire('pointermove', -500, -500)
    fire('pointerup', -500, -500)
    expect(hook.result.current.position).toEqual({ x: 12, y: 12 })
  })

  it('a drag suppresses the subsequent click, a plain press does not', () => {
    const hook = renderHook(() =>
      useDraggable({ initial: { x: 100, y: 100 }, getSize: () => ({ width: 54, height: 54 }) }),
    )

    startAt(hook, 110, 110)
    fire('pointermove', 200, 200)
    fire('pointerup', 200, 200)
    expect(hook.result.current.wasDragged()).toBe(true)

    startAt(hook, 200, 200)
    fire('pointerup', 200, 200) // no movement: a click
    expect(hook.result.current.wasDragged()).toBe(false)
  })

  it('re-clamps when the footprint grows (mode change)', () => {
    const hook = renderHook(
      ({ size }) => useDraggable({ initial: { x: 1300, y: 800 }, getSize: () => size }),
      { initialProps: { size: { width: 54, height: 54 } } },
    )

    // bubble-sized footprint fits at 1300/800 (clamped to 1374/834 area)
    expect(hook.result.current.position.x).toBeLessThanOrEqual(1374)

    hook.rerender({ size: { width: 960, height: 680 } })
    const { x, y } = hook.result.current.position
    expect(x).toBeLessThanOrEqual(window.innerWidth - 960 - 12)
    expect(y).toBeLessThanOrEqual(window.innerHeight - 680 - 12)
    expect(x).toBeGreaterThanOrEqual(12)
    expect(y).toBeGreaterThanOrEqual(12)
  })
})
