import { useCallback, useEffect, useMemo, useState } from 'react'
import { ConnectionScreen, ActionErrorToast } from './layout/ConnectionScreen'
import { DesktopStage } from './layout/DesktopStage'
import { DraggableWindow } from './layout/DraggableWindow'
import { GenosBubble } from './layout/GenosBubble'
import { HeaderBar } from './layout/HeaderBar'
import { Toasts } from './layout/Toasts'
import { CompactPanel } from './panels/CompactPanel'
import { ExpandedWorkspace } from './panels/ExpandedWorkspace'
import { useFloatingWindow, MODE_SIZE } from './hooks/useFloatingWindow'
import { useGenosConnection } from './hooks/useGenosConnection'
import { useGenosState } from './hooks/useGenosState'
import { useNotificationTimeouts } from './hooks/useNotificationTimeouts'
import { getDemoControls } from './services/demo'
import { genosService } from './services/genosService'
import type { ServiceError, ServiceResult } from './services/types'
import { STATUS_LABEL } from './types'

/**
 * Application root.
 *
 * Two responsibilities, nothing more:
 *   1. Gate the data-driven UI on the transport connection state.
 *   2. Mount the floating shell once the service is ready.
 *
 * All Genos data flows through `genosService`; demo-only controls are reached
 * via `getDemoControls()` and simply absent against a production service.
 */
export default function App() {
  const connection = useGenosConnection()

  useEffect(() => {
    void genosService.init()
  }, [])

  if (connection.status === 'error') {
    return (
      <ConnectionScreen
        state="error"
        error={connection.error}
        onRetry={() => void genosService.init()}
      />
    )
  }

  if (connection.status !== 'ready') {
    return <ConnectionScreen state="connecting" onRetry={() => void genosService.init()} />
  }

  return <FloatingShell />
}

/* ========================================================================== */

/** The floating companion. Mounted only while the connection is ready. */
function FloatingShell() {
  const state = useGenosState()
  const shell = useFloatingWindow()
  const { view, mode, railTab, setRailTab, windowDrag, bubbleDrag } = shell

  /* Demo controls exist only on the mock service; production gets `null`. */
  const demo = useMemo(() => getDemoControls(genosService), [])

  /* Typed integration errors surface as a calm, dismissible notice. */
  const [actionError, setActionError] = useState<ServiceError | null>(null)

  useEffect(() => {
    if (!actionError) return
    const timer = setTimeout(() => setActionError(null), 6000)
    return () => clearTimeout(timer)
  }, [actionError])

  const perform = useCallback((result: Promise<ServiceResult<void>>) => {
    void result.then((r) => {
      if (!r.ok) setActionError(r.error)
    })
  }, [])

  useNotificationTimeouts(
    useMemo(() => state.notifications.map((n) => n.id), [state.notifications]),
  )

  /* ------------------------------------------------------------ handlers */

  const onSend = useCallback((text: string) => perform(genosService.sendMessage(text)), [perform])
  const onApprove = useCallback(() => perform(genosService.approveAction()), [perform])
  const onDeny = useCallback(() => perform(genosService.denyAction()), [perform])
  const onResume = useCallback(() => perform(genosService.resumeWorkflow()), [perform])
  const onRetry = useCallback(() => perform(genosService.retryWorkflow()), [perform])
  const onRollback = useCallback(() => perform(genosService.requestRollback()), [perform])

  /* -------------------------------------------------------------- render */

  const needsAttention = state.status === 'waiting' || state.status === 'error'
  const toastAnchor = useMemo(() => {
    if (view === 'bubble') {
      return { left: Math.max(12, bubbleDrag.position.x - 280), top: bubbleDrag.position.y }
    }
    const size = MODE_SIZE[mode]
    const left = windowDrag.position.x - 280
    return {
      left: left > 12 ? left : Math.min(window.innerWidth - 280, windowDrag.position.x + size.width + 12),
      top: windowDrag.position.y + 44,
    }
  }, [view, mode, windowDrag.position, bubbleDrag.position])

  return (
    <>
      <DesktopStage onOpen={shell.openCompact} />

      <Toasts notifications={state.notifications} anchor={toastAnchor} />

      {actionError ? (
        <ActionErrorToast
          error={actionError}
          anchor={{ left: toastAnchor.left, top: toastAnchor.top + 8 }}
          onDismiss={() => setActionError(null)}
        />
      ) : null}

      {view === 'bubble' ? (
        <GenosBubble
          status={state.status}
          statusDetail={state.statusDetail}
          position={bubbleDrag.position}
          dragging={bubbleDrag.dragging}
          needsAttention={needsAttention}
          onDragStart={bubbleDrag.startDrag}
          onOpen={shell.onBubbleClick}
        />
      ) : (
        <DraggableWindow
          mode={mode}
          position={windowDrag.position}
          dragging={windowDrag.dragging}
          onDragStart={windowDrag.startDrag}
          titleBar={
            <HeaderBar
              mode={mode}
              project={state.project}
              status={state.status}
              statusDetail={state.statusDetail}
              onMinimize={shell.collapseToBubble}
              onToggleMode={shell.toggleMode}
              onClose={shell.closeGenos}
              titleId="genos-title"
            />
          }
        >
          {mode === 'compact' ? (
            <CompactPanel
              state={state}
              onSend={onSend}
              onApprove={onApprove}
              onDeny={onDeny}
              onResume={onResume}
              onRetry={onRetry}
              onRollback={onRollback}
              onExpand={shell.openExpanded}
              onInspectFailure={() => {
                setRailTab('activity')
                shell.openExpanded()
              }}
            />
          ) : (
            <ExpandedWorkspace
              state={state}
              railTab={railTab}
              onRailTabChange={setRailTab}
              onSend={onSend}
              onApprove={onApprove}
              onDeny={onDeny}
              onResume={onResume}
              onRetry={onRetry}
              onRollback={onRollback}
              demoScenario={demo?.getDemoScenario()}
              onDemoScenarioChange={demo ? (scenario) => demo.setDemoScenario(scenario) : undefined}
              onDemoReset={demo ? () => demo.reset() : undefined}
            />
          )}
        </DraggableWindow>
      )}

      <p className="sr-only" role="status" aria-live="polite">
        Genos: {STATUS_LABEL[state.status]}. {state.statusDetail}
      </p>
    </>
  )
}
