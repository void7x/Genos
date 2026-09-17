import { GenosMark, Icon, Tooltip } from '../components/ui'
import { StatusDot } from '../components/ui/Primitives'
import { GitStrip } from '../git/GitPanel'
import { STATUS_LABEL, type AgentStatus, type ProjectContext } from '../types'
import type { WindowMode } from './DraggableWindow'

interface HeaderBarProps {
  mode: WindowMode
  project: ProjectContext
  status: AgentStatus
  statusDetail: string
  onMinimize: () => void
  onToggleMode: () => void
  onClose: () => void
  titleId: string
}

/**
 * Header. Deliberately sparse: identity, project, branch, status, window
 * controls. Nothing else earns a place up here.
 */
export function HeaderBar({
  mode,
  project,
  status,
  statusDetail,
  onMinimize,
  onToggleMode,
  onClose,
  titleId,
}: HeaderBarProps) {
  const expanded = mode === 'expanded'

  return (
    <>
      <div className="titlebar__brand">
        <GenosMark size={16} />
        <span className="titlebar__name" id={titleId}>
          GENOS
        </span>
      </div>

      <span className="titlebar__sep" aria-hidden="true" />

      <div className="titlebar__meta">
        {/* Not a control: the project list is a backend concern, so this stays
            an indicator rather than a dead button. */}
        <span className="chip" title={`${project.name} · ${project.path}`}>
          <Icon name="folder" size={11} />
          <span>{project.name}</span>
        </span>

        {expanded ? <GitStrip git={project.gitState} /> : null}

        <span className="chip" title={`Genos is ${STATUS_LABEL[status].toLowerCase()}: ${statusDetail}`}>
          <StatusDot status={status} />
          <span>{STATUS_LABEL[status]}</span>
        </span>
      </div>

      <div className="titlebar__spacer" />

      <div className="window-controls" data-no-drag="true">
        <Tooltip label="Collapse to bubble (Esc)">
          <button type="button" className="win-btn" onClick={onMinimize} aria-label="Collapse Genos to bubble">
            <Icon name="minimize" size={14} />
          </button>
        </Tooltip>

        <Tooltip label={expanded ? 'Compact panel' : 'Expand workspace'}>
          <button
            type="button"
            className="win-btn"
            onClick={onToggleMode}
            aria-label={expanded ? 'Switch to compact panel' : 'Expand Genos workspace'}
          >
            <Icon name={expanded ? 'collapse' : 'expand'} size={13} />
          </button>
        </Tooltip>

        <Tooltip label="Close">
          <button
            type="button"
            className="win-btn"
            data-variant="close"
            onClick={onClose}
            aria-label="Close Genos"
          >
            <Icon name="close" size={14} />
          </button>
        </Tooltip>
      </div>
    </>
  )
}
