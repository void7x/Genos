import { useState } from 'react'
import { Composer } from '../chat/Composer'
import { MessageList } from '../chat/MessageList'
import { CodeBlock } from '../components/code/CodeBlock'
import { Button, Card, Details, EmptyState, Icon } from '../components/ui'
import { GitPanel } from '../git/GitPanel'
import { MemoryPanel } from '../memory/MemoryPanel'
import { ActionHistoryPanel } from './ActionHistoryPanel'
import { WorkspacePanel } from './WorkspacePanel'
import { TaskPanel } from '../tasks/TaskPanel'
import { PermissionCard } from '../workflow/PermissionCard'
import { RecoveryCard } from '../workflow/RecoveryCard'
import { RollbackCard } from '../workflow/RollbackCard'
import { StepList } from '../workflow/StepList'
import { VerificationCard } from '../workflow/VerificationCard'
import { WorkflowStages } from '../workflow/WorkflowStages'
import type { DemoScenario, GenosState } from '../types'

interface ExpandedWorkspaceProps {
  state: GenosState
  railTab?: 'activity' | 'context'
  onRailTabChange?: (tab: 'activity' | 'context') => void
  onSend: (text: string) => void
  onApprove: () => void
  onDeny: () => void
  onRollback: () => void
  /** Continue an interrupted workflow (distinct from retry). */
  onResume: () => void
  /** Restart a failed workflow from the beginning. */
  onRetry: () => void
  /* Demo-only props: provided exclusively by the mock-backed demo UI. */
  demoScenario?: DemoScenario
  onDemoScenarioChange?: (scenario: DemoScenario) => void
  onDemoReset?: () => void
}

const IDLE_SUGGESTIONS = [
  'Fix the failing tests in the memory resolver',
  'Inspect project',
  'Check Git',
  'What do you remember about this project?',
]

/**
 * The full Genos workspace.
 *
 * Left: context. Centre: conversation. Right: what Genos is doing and what it
 * proved. Still a floating panel, not an IDE replacement.
 */
export function ExpandedWorkspace({
  state,
  railTab = 'activity',
  onRailTabChange,
  onSend,
  onApprove,
  onDeny,
  onRollback,
  onResume,
  onRetry,
  demoScenario,
  onDemoScenarioChange,
  onDemoReset,
}: ExpandedWorkspaceProps) {
  const demoAvailable =
    demoScenario !== undefined && onDemoScenarioChange !== undefined && onDemoReset !== undefined
  const [internalTab, setInternalTab] = useState<'activity' | 'context'>('activity')
  const tab = onRailTabChange ? railTab : internalTab
  const setTab = onRailTabChange ?? setInternalTab
  const { workflow, permission, verification, recovery, rollback } = state
  const hasWorkflow = workflow.steps.length > 0

  return (
    <div className="workspace">
      {/* ------------------------------------------------------- left rail */}
      <aside className="workspace__rail workspace__rail--left" aria-label="Project context">
        <div className="selector" title="Active workspace">
          <Icon name="folder" size={15} style={{ color: 'var(--g-accent-2)' }} />
          <span style={{ minWidth: 0 }}>
            <span className="selector__name">{state.project.name}</span>
            <br />
            <span className="selector__path">{state.project.path}</span>
          </span>
          <span className="g-mono g-dim" style={{ marginLeft: 'auto', fontSize: 'var(--g-fs-micro)' }}>
            {state.project.language}
          </span>
        </div>

        <div className="rail-scroll">
          <WorkspacePanel project={state.project} files={state.files} />
          <GitPanel git={state.project.gitState} />
          <MemoryPanel memories={state.memories} />

          <div className="rail-footer">
          {demoAvailable ? (
            <div className="demo-note">
              <span>
                <strong style={{ color: 'var(--g-text-2)' }}>Prototype</strong> · mock service
                layer. Nothing is executed.
              </span>
              <span className="demo-note__row">
                {(['success', 'failure'] as DemoScenario[]).map((option) => (
                  <button
                    key={option}
                    type="button"
                    className="chip chip--button"
                    aria-pressed={demoScenario === option}
                    style={
                      demoScenario === option
                        ? { borderColor: 'var(--g-accent-line)', color: 'var(--g-accent-2)' }
                        : undefined
                    }
                    onClick={() => onDemoScenarioChange?.(option)}
                  >
                    {option === 'success' ? 'Happy path' : 'Failure path'}
                  </button>
                ))}
              </span>
              <Button size="sm" variant="ghost" icon="refresh" onClick={onDemoReset} block>
                Reset demo
              </Button>
            </div>
          ) : (
            <div className="demo-note">
              <span>
                Connected surface — every value on this panel comes from the
                active GenosService.
              </span>
            </div>
          )}
        </div>
        </div>
      </aside>

      <section className="workspace__main" aria-label="Conversation">
        <MessageList
          messages={state.messages}
          empty={
            <EmptyState
              title="What are we working on?"
              hint="Genos inspects the workspace, proposes a plan, asks before it writes, and verifies what it changed."
              actions={IDLE_SUGGESTIONS.map((s) => (
                <button key={s} type="button" className="chip chip--button" onClick={() => onSend(s)}>
                  {s}
                </button>
              ))}
            />
          }
        />
        <Composer
          onSend={onSend}
          working={state.busy}
          workingLabel={state.statusDetail}
          placeholder="Ask Genos to inspect your project…"
        />
      </section>

      <aside className="workspace__rail workspace__rail--right" aria-label="Task and verification">
        <div className="rail-tabs" role="tablist" aria-label="Right panel sections">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'activity'}
            onClick={() => setTab('activity')}
          >
            Activity
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'context'}
            onClick={() => setTab('context')}
          >
            Context
          </button>
        </div>

        <div className="rail-scroll">
        {tab === 'activity' ? (
          <>
            <Card title="Workflow" icon="activity" live="polite">
              <WorkflowStages workflow={workflow} />
            </Card>

            <Card title="Plan" icon="target">
              {hasWorkflow ? (
                <StepList steps={workflow.steps} />
              ) : (
                <p
                  className="g-mono g-dim"
                  style={{ margin: 0, fontSize: 'var(--g-fs-label)' }}
                >
                  No plan yet. Genos builds one after it inspects the workspace.
                </p>
              )}
              {workflow.interrupted || state.status === 'error' || rollback ? (
                <div className="notice__actions">
                  {workflow.interrupted ? (
                    <Button size="sm" variant="primary" icon="play" onClick={onResume}>
                      Resume workflow
                    </Button>
                  ) : null}
                  {state.status === 'error' || rollback ? (
                    <Button size="sm" icon="refresh" onClick={onRetry}>
                      Retry workflow
                    </Button>
                  ) : null}
                </div>
              ) : null}
            </Card>

            {permission ? (
              <PermissionCard request={permission} onApprove={onApprove} onDeny={onDeny} />
            ) : null}

            {verification ? (
              <VerificationCard result={verification} onInspectFailure={() => setTab('activity')} />
            ) : null}

            {verification?.failure ? (
              <Details summary="Raw failure output" defaultOpen>
                <CodeBlock code={verification.failure.output} language="text" variant="output" />
              </Details>
            ) : null}

            {recovery ? <RecoveryCard recovery={recovery} onRollback={onRollback} /> : null}

            {rollback ? <RollbackCard rollback={rollback} /> : null}

            <ActionHistoryPanel history={state.history} />
          </>
        ) : (
          <>
            <TaskPanel tasks={state.tasks} goal={state.goal} />
            <MemoryPanel memories={state.memories} />
            <ActionHistoryPanel history={state.history} limit={12} />
          </>
        )}
        </div>
      </aside>
    </div>
  )
}
