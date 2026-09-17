import { useCallback, useState } from 'react'
import type { WindowMode } from '../layout/DraggableWindow'
import { useDraggable } from './useDraggable'
import { useKeyboardShortcuts } from './useKeyboardShortcuts'

export type GenosView = 'bubble' | 'compact' | 'expanded'

/** Approximate rendered footprint per mode, used for clamping and anchoring. */
export const MODE_SIZE: Record<WindowMode, { width: number; height: number }> = {
  compact: { width: 376, height: 600 },
  expanded: { width: 960, height: 680 },
}

export const BUBBLE_SIZE = { width: 54, height: 54 }

/**
 * PURE PRESENTATION STATE — deliberately isolated from backend state.
 *
 * Everything here (which surface is visible, where it floats, which rail tab
 * is open) is UI-local. A future desktop shell (Tauri/Electron/PySide webview)
 * can take any of it over without touching the service layer:
 *
 *  - `view`/`mode` map to webview size/visibility controlled by the shell,
 *  - `position` maps to native window placement instead of CSS,
 *  - dragging maps to native window dragging instead of pointer events.
 *
 * The hook makes no assumption that the browser viewport equals a desktop
 * window manager: clamping only keeps the floating surface inside whatever
 * area the shell gave us.
 */
export function useFloatingWindow() {
  const [view, setView] = useState<GenosView>('bubble')
  const [mode, setMode] = useState<WindowMode>('compact')
  const [railTab, setRailTab] = useState<'activity' | 'context'>('activity')

  const getWindowSize = useCallback(() => MODE_SIZE[mode], [mode])
  const getBubbleSize = useCallback(() => BUBBLE_SIZE, [])

  const windowDrag = useDraggable({
    initial: {
      x: Math.max(12, window.innerWidth - MODE_SIZE.compact.width - 28),
      y: Math.max(12, window.innerHeight - MODE_SIZE.compact.height - 96),
    },
    getSize: getWindowSize,
  })

  const bubbleDrag = useDraggable({
    initial: { x: Math.max(12, window.innerWidth - 84), y: Math.max(12, window.innerHeight - 150) },
    getSize: getBubbleSize,
  })

  const openCompact = useCallback(() => {
    setMode('compact')
    windowDrag.move(bubbleDrag.position)
    setView('compact')
  }, [bubbleDrag.position, windowDrag])

  const openExpanded = useCallback(() => {
    setMode('expanded')
    setRailTab('activity')
    windowDrag.move(windowDrag.position)
    setView('expanded')
  }, [windowDrag])

  const collapseToBubble = useCallback(() => {
    bubbleDrag.move(windowDrag.position)
    setView('bubble')
  }, [bubbleDrag, windowDrag.position])

  const closeGenos = useCallback(() => {
    setView('bubble')
  }, [])

  useKeyboardShortcuts({
    onToggle: () => setView((v) => (v === 'bubble' ? 'compact' : 'bubble')),
    onExpand: () => {
      setMode('expanded')
      setView('expanded')
    },
    onCollapse: () => {
      if (view !== 'bubble') collapseToBubble()
    },
  })

  const onBubbleClick = useCallback(() => {
    // A drag that ends on the bubble must not open the panel.
    if (bubbleDrag.wasDragged()) return
    openCompact()
  }, [bubbleDrag, openCompact])

  const toggleMode = useCallback(() => {
    if (mode === 'compact') openExpanded()
    else setMode('compact')
  }, [mode, openExpanded])

  return {
    view,
    mode,
    railTab,
    setRailTab,
    windowDrag,
    bubbleDrag,
    openCompact,
    openExpanded,
    collapseToBubble,
    closeGenos,
    onBubbleClick,
    toggleMode,
  }
}
