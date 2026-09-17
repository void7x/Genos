import { useSyncExternalStore } from 'react'
import { genosService } from '../services/genosService'
import type { ConnectionState } from '../services/types'

/**
 * React binding for the transport lifecycle.
 *
 * The shell gates on this: `connecting` shows a loading surface, `error`
 * shows a retry surface, and only `ready` mounts the data-driven UI. This is
 * what keeps `getState()` from ever throwing inside a render.
 */
export function useGenosConnection(): ConnectionState {
  return useSyncExternalStore(
    genosService.subscribe,
    genosService.getConnectionState,
    genosService.getConnectionState,
  )
}
