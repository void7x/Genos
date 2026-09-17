import { Icon, ProgressBar, type IconName } from '../components/ui'
import { percent } from '../utils/format'
import type { WorkflowPhaseStatus, WorkflowSnapshot } from '../types'

const PHASE_ICON: Record<WorkflowPhaseStatus, IconName> = {
  pending: 'circle',
  active: 'spinner',
  done: 'check',
  failed: 'x',
  skipped: 'circle',
}

/**
 * Plan → Approval → Execute → Verify → Complete.
 * Must be readable in under a second, from the corner of the eye.
 */
export function WorkflowStages({ workflow }: { workflow: WorkflowSnapshot }) {
  const active = workflow.phases.find((p) => p.status === 'active')
  const allDone = workflow.phases.every((p) => p.status === 'done')

  return (
    <div>
      <div className="workflow-stages">
        {workflow.phases.map((phase) => (
          <div className="stage" data-status={phase.status} key={phase.stage}>
            <span className="stage__icon">
              <Icon
                name={PHASE_ICON[phase.status]}
                size={9}
                style={phase.status === 'active' ? { animation: 'g-spin 1.1s linear infinite' } : undefined}
              />
            </span>
            <span>{phase.label}</span>
            <span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-micro)' }}>
              {phase.status === 'done' ? 'ok' : phase.status === 'active' ? 'now' : phase.status}
            </span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 9, display: 'flex', flexDirection: 'column', gap: 5 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span className="g-label">Progress</span>
          <span className="g-mono" style={{ color: 'var(--g-text-2)' }}>
            {percent(workflow.progress)}
          </span>
        </div>
        <ProgressBar
          value={workflow.progress}
          label="Workflow progress"
          tone={workflow.phases.some((p) => p.status === 'failed') ? 'err' : 'accent'}
        />
        <span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-label)' }}>
          {active
            ? `Stage: ${active.label}`
            : workflow.interrupted
              ? 'Workflow paused · resumable'
              : allDone
                ? 'Workflow complete'
                : 'Workflow idle'}
          {workflow.resumable ? ' · resumable' : ''}
        </span>
      </div>
    </div>
  )
}
