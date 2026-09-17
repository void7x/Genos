import { useSyncExternalStore } from 'react'
import { genosService } from '../services/genosService'
import type { GenosState } from '../types'

/**
 * React binding to the service layer.
 *
 * Subscribes to whatever `genosService` currently resolves to, so the mock and
 * a future backend behave identically from a component's point of view.
 */
export function useGenosState(): GenosState {
  return useSyncExternalStore(genosService.subscribe, genosService.getState, genosService.getState)
}
