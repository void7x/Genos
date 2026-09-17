import { useEffect, useRef } from 'react'
import { genosService } from '../services/genosService'

/**
 * Dismisses each notification once, `ttlMs` after it first appeared.
 * Uses a per-id timer so a new notification never resets an older one.
 */
export function useNotificationTimeouts(ids: string[], ttlMs = 6000) {
  const scheduled = useRef<Set<string>>(new Set())

  useEffect(() => {
    const fresh = ids.filter((id) => !scheduled.current.has(id))
    fresh.forEach((id) => {
      scheduled.current.add(id)
      setTimeout(() => genosService.dismissNotification(id), ttlMs)
    })
    // Intentionally no cleanup: timers must fire even when new notifications
    // arrive later (otherwise earlier toasts would live forever).
  }, [ids, ttlMs])
}
