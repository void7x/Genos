import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { Button, Icon, Tooltip } from '../components/ui'

interface ComposerProps {
  onSend: (text: string) => void
  /** Genos is mid-workflow: composer stays usable but signals the busy state. */
  working?: boolean
  workingLabel?: string
  placeholder?: string
  compact?: boolean
  /** Suggestion chips rendered under the input when it is empty. */
  suggestions?: string[]
  autoFocus?: boolean
  id?: string
}

const SUGGESTION_LIMIT = 4

/**
 * The conversational input. Multiline, Enter to send, Shift+Enter for a new
 * line, visible focus state, disabled and working presentations.
 */
export function Composer({
  onSend,
  working = false,
  workingLabel,
  placeholder = 'Ask Genos to inspect your project…',
  compact = false,
  suggestions = [],
  autoFocus = false,
  id,
}: ComposerProps) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)
  const areaRef = useRef<HTMLTextAreaElement>(null)
  const generatedId = useId()
  const inputId = id ?? generatedId
  const disabled = false

  const resize = useCallback(() => {
    const el = areaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, compact ? 150 : 190)}px`
  }, [compact])

  useEffect(resize, [value, resize])

  useEffect(() => {
    if (autoFocus) areaRef.current?.focus()
  }, [autoFocus])

  const submit = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
    requestAnimationFrame(resize)
  }

  const onKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  const showSuggestions = value.trim().length === 0 && suggestions.length > 0

  return (
    <div className={['composer', compact ? 'composer--compact' : ''].filter(Boolean).join(' ')}>
      <div className="composer__box" data-disabled={disabled} data-focused={focused}>
        <label className="sr-only" htmlFor={inputId}>
          Message Genos
        </label>
        <textarea
          id={inputId}
          ref={areaRef}
          className="composer__input"
          rows={compact ? 2 : 3}
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          aria-busy={working}
          aria-describedby={`${inputId}-hint`}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />

        <div className="composer__bar">
          <Tooltip label="Attach workspace context">
            <button type="button" className="icon-btn" aria-label="Attach workspace context">
              <Icon name="attach" size={13} />
            </button>
          </Tooltip>

          <Tooltip label="Insert a slash command">
            <button
              type="button"
              className="icon-btn"
              aria-label="Insert a slash command"
              onClick={() => setValue((v) => (v.endsWith('/') || v === '' ? `${v}/` : `${v} /`))}
            >
              <Icon name="terminal" size={13} />
            </button>
          </Tooltip>

          {working ? (
            <span className="composer__state" aria-live="polite">
              <Icon name="spinner" size={12} style={{ animation: 'g-spin 1.1s linear infinite' }} />
              {workingLabel ?? 'Genos is working'}
            </span>
          ) : (
            <span className="composer__hint" id={`${inputId}-hint`}>
              <kbd className="btn__kbd">↵</kbd> send
              <span className="g-dim">·</span>
              <kbd className="btn__kbd">⇧↵</kbd> newline
            </span>
          )}

          <Button
            className="send-btn"
            variant="ghost"
            onClick={submit}
            disabled={disabled || value.trim().length === 0}
            aria-label="Send message to Genos"
            title="Send (Enter)"
          >
            <Icon name="send" size={14} />
          </Button>
        </div>
      </div>

      {showSuggestions ? (
        <div className="empty__actions" style={{ marginTop: 7, justifyContent: 'flex-start' }}>
          {suggestions.slice(0, SUGGESTION_LIMIT).map((s) => (
            <button
              key={s}
              type="button"
              className="chip chip--button"
              onClick={() => {
                onSend(s)
              }}
            >
              {s}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
