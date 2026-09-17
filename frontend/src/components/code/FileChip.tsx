import type { FileChangeState, FileReference } from '../../types'

const TONE: Record<FileChangeState, string> = {
  original: 'var(--g-text-3)',
  modified: 'var(--g-warn)',
  added: 'var(--g-ok)',
  deleted: 'var(--g-err)',
}

const SYMBOL: Record<FileChangeState, string> = {
  original: '·',
  modified: 'M',
  added: 'A',
  deleted: 'D',
}

/** A single referenced project file, with optional line hint and change mark. */
export function FileChip({ file }: { file: FileReference }) {
  const change = file.change ?? 'original'
  return (
    <div className="msg__file" data-change={change}>
      <span style={{ color: TONE[change], fontFamily: 'var(--g-mono)' }}>{SYMBOL[change]}</span>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }} title={file.path}>
        {file.path}
      </span>
      {file.line ? <span className="msg__file-line">:{file.line}</span> : null}
    </div>
  )
}
