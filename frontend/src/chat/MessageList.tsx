import { useEffect, useRef } from 'react'
import { Message } from './Message'
import type { ChatMessage } from '../types'

interface MessageListProps {
  messages: ChatMessage[]
  /** Compact mode shows only the tail of the conversation. */
  limit?: number
  className?: string
  id?: string
  empty?: React.ReactNode
}

/**
 * Scrollable conversation. Auto-follows new content unless the developer has
 * scrolled up to read history.
 */
export function MessageList({ messages, limit, className = '', id, empty }: MessageListProps) {
  const ref = useRef<HTMLDivElement>(null)
  const pinned = useRef(true)
  const shown = limit ? messages.slice(-limit) : messages

  useEffect(() => {
    const el = ref.current
    if (!el || !pinned.current) return
    el.scrollTop = el.scrollHeight
  }, [messages.length, shown.length])

  const onScroll = () => {
    const el = ref.current
    if (!el) return
    pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40
  }

  return (
    <div
      ref={ref}
      id={id}
      className={['thread', className].filter(Boolean).join(' ')}
      role="log"
      aria-label="Genos conversation"
      aria-relevant="additions"
      tabIndex={0}
      onScroll={onScroll}
    >
      {shown.length === 0 ? empty : shown.map((m) => <Message key={m.id} message={m} />)}
    </div>
  )
}
