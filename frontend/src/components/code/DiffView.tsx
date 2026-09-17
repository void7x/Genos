import { Chip, Icon } from '../ui'
import type { FileChangeState, FileDiff } from '../../types'

const CHANGE_LABEL: Record<FileChangeState, string> = {
  original: 'Original',
  modified: 'Modified',
  added: 'Added',
  deleted: 'Deleted',
}

const CHANGE_TONE: Record<FileChangeState, 'default' | 'warn' | 'ok' | 'err'> = {
  original: 'default',
  modified: 'warn',
  added: 'ok',
  deleted: 'err',
}

/**
 * Compact diff display. Deliberately not a code editor — Genos points at
 * changes, the developer edits in their IDE.
 */
export function DiffView({ diff }: { diff: FileDiff }) {
  const added = diff.lines.filter((l) => l.type === 'add').length
  const removed = diff.lines.filter((l) => l.type === 'remove').length

  return (
    <div className="diff">
      <div className="diff__head">
        <Icon name="diff" size={12} style={{ color: 'var(--g-text-4)' }} />
        <span className="diff__path" title={diff.path}>
          {diff.path}
        </span>
        <span className="diff__stats">
          <span className="diff__add">+{added}</span>
          <span className="diff__del">−{removed}</span>
        </span>
      </div>
      <div className="diff__rows" role="group" aria-label={`Diff for ${diff.path}`}>
        {diff.lines.map((line, i) => (
          <div className="diff__row" data-type={line.type} key={i}>
            <span className="diff__no">{line.oldNo ?? ''}</span>
            <span className="diff__no">{line.newNo ?? ''}</span>
            <span className="diff__sign">
              {line.type === 'add' ? '+' : line.type === 'remove' ? '−' : ' '}
            </span>
            <span className="diff__text">{line.text || ' '}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function FileStateChip({ state }: { state: FileChangeState }) {
  return <Chip tone={CHANGE_TONE[state]}>{CHANGE_LABEL[state]}</Chip>
}
