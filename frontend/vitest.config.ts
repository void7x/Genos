import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

/**
 * Test runner configuration, kept separate from `vite.config.ts` so the
 * app's dev-server policy never leaks into tests (and vice versa).
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['src/test/setup.ts'],
    restoreMocks: true,
    testTimeout: 20000,
  },
})
