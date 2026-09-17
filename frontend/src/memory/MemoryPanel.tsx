import { useMemo, useState } from 'react'
import { Card, Icon } from '../components/ui'
import type { MemoryEntry } from '../types'

/** Project memory: searchable, compact, expandable. Nothing heavier. */
export function MemoryPanel({ memories }: { memories: MemoryEntry[] }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return memories
    return memories.filter(
      (m) => m.text.toLowerCase().includes(q) || m.source.toLowerCase().includes(q),
    )
  }, [memories, query])

  return (
    <Card
      title="Memory"
      icon="memory"
      actions={
        <span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-label)' }}>
          {memories.length} stored
        </span>
      }
    >
      <div className="memory-search">
        <Icon name="search" size={12} style={{ color: 'var(--g-text-4)' }} />
        <input
          type="search"
          value={query}
          placeholder="Search memory…"
          aria-label="Search project memory"
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <p className="g-mono g-dim" style={{ margin: 0, fontSize: 'var(--g-fs-label)' }}>
          No memory matches “{query}”.
        </p>
      ) : (
        filtered.map((memory) => {
          const isOpen = open === memory.id
          return (
            <div className="memory-item" data-open={isOpen} key={memory.id}>
              <button
                type="button"
                className="memory-item__head"
                aria-expanded={isOpen}
                onClick={() => setOpen(isOpen ? null : memory.id)}
              >
                <Icon
                  name="chevron"
                  size={11}
                  style={{
                    marginTop: 2,
                    color: 'var(--g-text-4)',
                    transform: isOpen ? 'rotate(90deg)' : 'none',
                    transition: 'transform 120ms var(--g-ease)',
                  }}
                />
                <span>{memory.text}</span>
              </button>
              {isOpen ? (
                <>
                  <div className="memory-item__body">
                    Scope: {memory.scope}. Recorded from {memory.source}.
                  </div>
                  <div className="memory-item__meta">
                    <span>{memory.source}</span>
                    <span>·</span>
                    <span>{memory.at}</span>
                  </div>
                </>
              ) : (
                <div className="memory-item__meta">
                  <span>{memory.scope}</span>
                  <span>·</span>
                  <span>{memory.at}</span>
                </div>
              )}
            </div>
          )
        })
      )}
    </Card>
  )
}
