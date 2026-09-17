import { Icon, type IconName } from '../components/ui'
import type { GenosNotification, NotificationTone } from '../types'

const TONE_ICON: Record<NotificationTone, IconName> = {
  info: 'info',
  success: 'check',
  warning: 'alert',
  error: 'alert',
}

/**
 * Subtle desktop-style notifications.
 *
 * They appear near the Genos window, never as a browser-style banner, and are
 * announced politely to assistive tech.
 */
export function Toasts({
  notifications,
  anchor,
}: {
  notifications: GenosNotification[]
  anchor: { left: number; top: number }
}) {
  if (notifications.length === 0) return null

  return (
    <div
      className="toasts"
      style={{ left: anchor.left, top: anchor.top }}
      role="status"
      aria-live="polite"
      aria-label="Genos notifications"
    >
      {notifications.slice(-3).map((note) => (
        <div className="toast" data-tone={note.tone} key={note.id}>
          <span className="toast__icon">
            <Icon name={TONE_ICON[note.tone]} size={14} />
          </span>
          <div>
            <div className="toast__title">{note.title}</div>
            {note.body ? <div className="toast__body">{note.body}</div> : null}
          </div>
        </div>
      ))}
    </div>
  )
}
