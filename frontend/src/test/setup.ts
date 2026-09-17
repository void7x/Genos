/**
 * Test environment setup (jsdom).
 *
 * Adds the few browser APIs the floating UI relies on that jsdom lacks, and
 * resets the mock service between tests so each case starts from the seeded
 * session.
 */
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import { genosService } from '../services/genosService'
import { getDemoControls } from '../services/demo'

if (typeof window !== 'undefined') {
  if (!window.matchMedia) {
    window.matchMedia = ((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia
  }

  // jsdom has no layout: give pointer-event code something sane to clamp to.
  Object.defineProperty(window, 'innerWidth', { value: 1440, writable: true })
  Object.defineProperty(window, 'innerHeight', { value: 900, writable: true })

  if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = () => undefined
    Element.prototype.releasePointerCapture = () => undefined
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => undefined
  }
}

afterEach(() => {
  cleanup()
  const demo = getDemoControls(genosService)
  demo?.reset()
})
