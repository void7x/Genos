import { Button, Card, Chip, KeyValue } from '../components/ui'
import { durationLabel } from '../utils/format'
import type { FileReference, ProjectContext } from '../types'

/** Project context. Everything arrives through the service layer. */
export function WorkspacePanel({
  project,
  files,
}: {
  project: ProjectContext
  files: FileReference[]
}) {
  const tests = project.tests

  return (
    <>
      <Card title="Project" icon="folder">
        <dl style={{ margin: 0 }}>
          <KeyValue label="Name">{project.name}</KeyValue>
          <KeyValue label="Type">{project.language}</KeyValue>
          <KeyValue label="Branch">
            <span className="g-mono">{project.gitState.branch}</span>
          </KeyValue>
          <KeyValue label="Git">
            {project.gitState.clean ? 'Clean' : `${project.gitState.modifiedFiles} modified`}
          </KeyValue>
          <KeyValue label="Tests">
            <span style={{ color: tests.failed > 0 ? 'var(--g-err)' : 'var(--g-ok)' }}>
              {tests.passed} passed
              {tests.failed > 0 ? ` · ${tests.failed} failed` : ''}
            </span>
          </KeyValue>
          <KeyValue label="Last run">
            <span className="g-mono">
              {tests.lastRun} · {durationLabel(tests.durationMs)}
            </span>
          </KeyValue>
        </dl>
        <div style={{ marginTop: 8, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
          <Chip mono title={project.path}>
            {project.path}
          </Chip>
          <Chip>{project.workspace}</Chip>
        </div>
      </Card>

      <Card title="Relevant files" icon="file">
        <div>
          {files.map((file) => (
            <div className="file-row" data-change={file.change ?? 'original'} key={file.path}>
              <span className="file-row__path" title={file.path}>
                {file.path}
                {file.line ? `:${file.line}` : ''}
              </span>
              <span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-micro)' }}>
                {file.change && file.change !== 'original'
                  ? file.change[0].toUpperCase()
                  : '·'}
              </span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 8 }}>
          <Button size="sm" variant="ghost" icon="search" block>
            Inspect project
          </Button>
        </div>
      </Card>
    </>
  )
}
