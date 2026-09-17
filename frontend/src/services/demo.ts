/**
 * DEMO-ONLY CONTROLS — strictly separated from the production contract.
 *
 * The real Genos backend has no "demo scenario" and no "reset the demo".
 * Those capabilities exist only to exercise the UI without a backend, so they
 * live outside `GenosService` (see `./types`).
 *
 * Demo UI asks `getDemoControls(service)` and renders itself *only* when the
 * active service actually provides them. A production service simply does not
 * have these methods, and the demo affordances disappear — no fake
 * implementations are added to satisfy the UI.
 */
import type { DemoScenario } from '../types'
import type { GenosService } from './types'

export interface DemoControls {
  setDemoScenario(scenario: DemoScenario): void
  getDemoScenario(): DemoScenario
  reset(): void
}

/** Structural check — the production service fails it and stays clean. */
export function getDemoControls(service: GenosService): DemoControls | null {
  const candidate = service as Partial<DemoControls>
  if (
    typeof candidate.setDemoScenario === 'function' &&
    typeof candidate.getDemoScenario === 'function' &&
    typeof candidate.reset === 'function'
  ) {
    return service as GenosService & DemoControls
  }
  return null
}
