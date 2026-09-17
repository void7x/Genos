import { Card, Chip, Icon, KeyValue } from '../components/ui'
import type { GitState } from '../types'

/** Minimal, glanceable Git context. */
export function GitPanel({ git }: { git: GitState }) {
  const clean = git.clean

  return (
    <Card title="Git" icon="branch">
      <div className="git-summary">
        <Icon name="branch" size={13} style={{ color: 'var(--g-cool)' }} />
        <span className="git-summary__branch">{git.branch}</span>
        <span style={{ marginLeft: 'auto' }}>
          <Chip tone={clean ? 'ok' : 'warn'}>{clean ? 'Clean' : `${git.modifiedFiles} modified`}</Chip>
        </span>
      </div>

      <dl style={{ margin: '8px 0 0' }}>
        <KeyValue label="Last commit">
          <span className="g-mono">{git.lastCommit}</span>
        </KeyValue>
        <KeyValue label="Sync">
          <span className="g-mono">
            {git.ahead === 0 && git.behind === 0 ? 'up to date' : `↑${git.ahead} ↓${git.behind}`}
          </span>
        </KeyValue>
      </dl>
    </Card>
  )
}

/** Compact one-line Git strip for the header. */
export function GitStrip({ git }: { git: GitState }) {
  return (
    <span className="chip chip--mono" title={`Branch ${git.branch}`}>
      <Icon name="branch" size={11} />
      <span>{git.branch}</span>
      {git.clean ? null : (
        <span style={{ color: 'var(--g-warn)' }}>· {git.modifiedFiles}</span>
      )}
    </span>
  )
}
