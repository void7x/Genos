import { useEffect } from 'react'

export interface ShortcutHandlers {
  onToggle: () => void
  onExpand: () => void
  onCollapse: () => void
}

/**
 * Global shortcuts for the floating companion.
 *
 *   Mod+J        open / close Genos
 *   Mod+Shift+J  expand the workspace
 *   Escape       collapse to the bubble (only when focus is outside a field)
 */
export function useKeyboardShortcuts({ onToggle, onExpand, onCollapse }: ShortcutHandlers) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const mod = event.metaKey || event.ctrlKey
      const key = event.key.toLowerCase()

      if (mod && key === 'j') {
        event.preventDefault()
        if (event.shiftKey) onExpand()
        else onToggle()
        return
      }

      if (event.key === 'Escape') {
        const el = document.activeElement as HTMLElement | null
        const typing =
          el &&
          (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)
        if (typing) {
          el?.blur()
          return
        }
        onCollapse()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onToggle, onExpand, onCollapse])
}
