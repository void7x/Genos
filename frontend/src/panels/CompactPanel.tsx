import { Composer } from '../chat/Composer'
import { MessageList } from '../chat/MessageList'
import { Button, Card, Icon, KeyValue, ProgressBar, StatusDot, ThinkingDots } from '../components/ui'
import { GitStrip } from '../git/GitPanel'
import { PermissionCard } from '../workflow/PermissionCard'
import { RecoveryCard } from '../workflow/RecoveryCard'
import { RollbackCard } from '../workflow/RollbackCard'
import { StepList } from '../workflow/StepList'
import { STATUS_LABEL, type GenosState } from '../types'

interface CompactPanelProps {
  state: GenosState
  onSend: (text: string) => void
  onApprove: () => void
  onDeny: () => void
  /** Continue an interrupted workflow (distinct from retry). */
  onResume: () => void
  /** Restart a failed workflow from the beginning. */
  onRetry: () => void
  onRollback: () => void
  onExpand: () => void
  onInspectFailure: () => void
}

const IDLE_SUGGESTIONS = ['Inspect project', 'Run tests', 'Check Git', 'Create a task']

/**
 * Compact Genos: the glanceable assistant.
 *
 * Status, current task, activity, and the input. Nothing that belongs in the
 * expanded workspace is repeated here.
 */
export function CompactPanel({
  state,
  onSend,
  onApprove,
  onDeny,
  onResume,
  onRetry,
  onRollback,
  onExpand,
  onInspectFailure,
}: CompactPanelProps) {
  const { workflow, permission, verification, recovery, rollback, project } = state
  const steps = workflow.steps
  const doneCount = steps.filter((s) => s.status === 'completed').length
  const idle = steps.length === 0
  const failed = workflow.phases.some((phase) => phase.status === 'failed') && !rollback

  return (
    <>
      <div className="compact">
        <div className="status-strip">
          <StatusDot status={state.status} label={STATUS_LABEL[state.status]} />
          <div className="status-strip__text">
            <div className="status-strip__title">
              {state.status === 'working' || state.status === 'thinking' ? (
                <span style={{ display: 'inline-flex', gap: 7, alignItems: 'center' }}>
                  {STATUS_LABEL[state.status]}
                  <ThinkingDots label={state.statusDetail} />
                </span>
              ) : (
                STATUS_LABEL[state.status]
              )}
            </div>
            <div className="status-strip__sub">
              {state.statusDetail} · {project.name} · {project.language}
            </div>
          </div>
          <div className="status-strip__right">
            <GitStrip git={project.gitState} />
          </div>
        </div>

        {permission ? (
          <PermissionCard request={permission} onApprove={onApprove} onDeny={onDeny} />
        ) : null}

        <Card title="Current task" icon="activity" live="polite">
          {idle ? (
            <>
              <div style={{ fontSize: 'var(--g-fs-md)', color: 'var(--g-text)' }}>
                What are we working on?
              </div>
              <p className="g-muted" style={{ margin: '4px 0 0', fontSize: 'var(--g-fs-sm)' }}>
                No active workflow. Describe a task and Genos will plan it, ask before writing, and
                verify the result.
              </p>
              <dl style={{ margin: '8px 0 0' }}>
                <KeyValue label="Project">{project.name}</KeyValue>
                <KeyValue label="Branch">
                  <span className="g-mono">{project.gitState.branch}</span>
                </KeyValue>
                <KeyValue label="Status">Ready</KeyValue>
              </dl>
            </>
          ) : (
            <>
              <div style={{ fontSize: 'var(--g-fs-md)', color: 'var(--g-text)' }}>
                {workflow.name}
              </div>
              <div
                className="g-mono"
                style={{
                  fontSize: 'var(--g-fs-label)',
                  color: 'var(--g-text-4)',
                  margin: '3px 0 7px',
                }}
              >
                Step {Math.min(doneCount + 1, steps.length)} of {steps.length} ·{' '}
                {workflow.phases.find((p) => p.status === 'active')?.label ?? workflow.phase}
              </div>
              <ProgressBar
                value={workflow.progress}
                label="Current task progress"
                tone={workflow.phases.some((p) => p.status === 'failed') ? 'err' : 'accent'}
              />
              {workflow.interrupted || failed ? (
                <div className="notice__actions">
                  {/* Interrupted ⇒ resume. Failed ⇒ retry. Never both. */}
                  {workflow.interrupted ? (
                    <Button size="sm" variant="primary" icon="play" onClick={onResume}>
                      Resume workflow
                    </Button>
                  ) : null}
                  {failed && !workflow.interrupted ? (
                    <Button size="sm" icon="refresh" onClick={onRetry}>
                      Retry workflow
                    </Button>
                  ) : null}
                </div>
              ) : null}
            </>
          )}
        </Card>

        {steps.length > 0 ? (
          <Card title="Activity" icon="activity">
            <StepList steps={steps} />
          </Card>
        ) : null}

        {verification ? (
          <Card
            title={verification.passed ? 'Task completed' : 'Verification failed'}
            icon={verification.passed ? 'check' : 'alert'}
            tone={verification.passed ? 'ok' : 'err'}
            live="polite"
          >
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {verification.checks.map((check) => (
                <li className="check" data-status={check.status} key={check.id}>
                  <span className="check__icon">
                    <Icon
                      name={
                        check.status === 'passed'
                          ? 'check'
                          : check.status === 'failed'
                            ? 'x'
                            : 'circle'
                      }
                      size={12}
                    />
                  </span>
                  <span className="check__label">{check.label}</span>
                </li>
              ))}
            </ul>
            <div className="notice__actions">
              <Button
                size="sm"
                variant={verification.passed ? 'primary' : 'default'}
                icon={verification.passed ? 'diff' : 'eye'}
                onClick={verification.passed ? onExpand : onInspectFailure}
              >
                {verification.passed ? 'View changes' : 'View failure'}
              </Button>
            </div>
          </Card>
        ) : null}

        {recovery ? (
          <RecoveryCard
            recovery={recovery}
            onInspect={onInspectFailure}
            onRollback={onRollback}
          />
        ) : null}

        {rollback ? <RollbackCard rollback={rollback} /> : null}

        {state.messages.length > 0 ? (
          <Card title="Conversation" icon="terminal">
            <MessageList messages={state.messages} limit={3} className="thread--compact" />
          </Card>
        ) : null}
      </div>

      <Composer
        onSend={onSend}
        compact
        working={state.busy}
        workingLabel={state.statusDetail}
        placeholder={
          idle ? 'Describe a task for Genos…' : 'Ask Genos about this task…'
        }
        suggestions={idle ? IDLE_SUGGESTIONS : []}
      />
    </>
  )
}
