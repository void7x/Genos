import { Icon, type IconName } from '../components/ui'
import type { PlanStep, StepStatus } from '../types'

const STATUS_ICON: Record<StepStatus, IconName> = {
  pending: 'circle',
  running: 'spinner',
  completed: 'check',
  failed: 'x',
  blocked: 'stop',
  waiting: 'clock',
}

const STATUS_TEXT: Record<StepStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Done',
  failed: 'Failed',
  blocked: 'Blocked',
  waiting: 'Approval',
}

function StepIcon({ status, index }: { status: StepStatus; index: number }) {
  if (status === 'pending') {
    return <span className="step__icon">{index}</span>
  }
  return (
    <span className="step__icon">
      <Icon
        name={STATUS_ICON[status]}
        size={10}
        style={status === 'running' ? { animation: 'g-spin 1.1s linear infinite' } : undefined}
      />
    </span>
  )
}

/**
 * The task plan. States are never colour-only: every step carries an icon and a
 * text label alongside its colour.
 */
export function StepList({ steps, showState = true }: { steps: PlanStep[]; showState?: boolean }) {
  if (steps.length === 0) {
    return (
      <p className="g-muted g-mono" style={{ margin: 0, fontSize: 'var(--g-fs-label)' }}>
        No plan yet — ask Genos for a task.
      </p>
    )
  }

  return (
    <ol className="steps" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
      {steps.map((step) => (
        <li className="step" data-status={step.status} key={step.id}>
          <StepIcon status={step.status} index={step.index} />
          <div className="step__body">
            <div className="step__title">{step.title}</div>
            {step.detail ? <div className="step__detail">{step.detail}</div> : null}
            {step.command ? (
              <div className="step__detail" style={{ color: 'var(--g-cool)' }}>
                $ {step.command}
              </div>
            ) : null}
          </div>
          {showState ? <span className="step__state">{STATUS_TEXT[step.status]}</span> : null}
        </li>
      ))}
    </ol>
  )
}
