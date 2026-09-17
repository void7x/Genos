import type { GenosState } from '../types'
import {
  GenosTransportError,
  type GenosCommand,
  type GenosTransport,
} from './transport'
import type { ServiceErrorCode } from './types'

const DEFAULT_BASE_URL = 'http://127.0.0.1:8787/api/v1'
const POLL_MS = 1000

const baseUrl = (import.meta.env.VITE_GENOS_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '')

interface StateEnvelope {
  ok: true
  state: GenosState
}

interface ErrorEnvelope {
  ok: false
  error?: { code?: string; message?: string }
}

const knownErrorCodes = new Set<ServiceErrorCode>([
  'permission-denied',
  'invalid-request',
  'backend-unavailable',
  'conflict',
  'timeout',
  'unknown',
])

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 8000)
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })

    const body = (await response.json().catch(() => null)) as StateEnvelope | ErrorEnvelope | null
    if (!response.ok || !body || body.ok === false) {
      const code = body && 'error' in body ? body.error?.code : undefined
      const message = body && 'error' in body ? body.error?.message : undefined
      const typedCode: ServiceErrorCode = code && knownErrorCodes.has(code as ServiceErrorCode)
        ? (code as ServiceErrorCode)
        : 'backend-unavailable'
      throw new GenosTransportError(
        typedCode,
        message || `Genos backend returned HTTP ${response.status}.`,
      )
    }
    return body as T
  } catch (cause) {
    if (cause instanceof GenosTransportError) throw cause
    throw cause
  } finally {
    window.clearTimeout(timeout)
  }
}

export const realGenosTransport: GenosTransport = (() => {
  let timer: number | null = null
  let active = true
  const listeners = new Set<(state: GenosState) => void>()

  const publish = (state: GenosState) => listeners.forEach((listener) => listener(state))

  const poll = async () => {
    if (!active) return
    try {
      const payload = await request<StateEnvelope>('/state')
      publish(payload.state)
    } catch {
      // Background polling stays quiet; the initial fetch exposes connection errors.
    } finally {
      if (active) timer = window.setTimeout(poll, POLL_MS)
    }
  }

  return {
    async fetchState() {
      const payload = await request<StateEnvelope>('/state')
      active = true
      if (timer !== null) window.clearTimeout(timer)
      timer = window.setTimeout(poll, POLL_MS)
      return payload.state
    },

    onState(listener) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
        if (listeners.size === 0 && timer !== null) {
          active = false
          window.clearTimeout(timer)
          timer = null
        }
      }
    },

    async command(command: GenosCommand) {
      const payload = await request<{ ok: true; state: GenosState }>('/command', {
        method: 'POST',
        body: JSON.stringify(command),
      })
      publish(payload.state)
    },
  }
})()
