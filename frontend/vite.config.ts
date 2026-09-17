import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * DEV vs PRODUCTION HOST POLICY
 * ----------------------------
 * GENOS is a *local desktop companion*: by default the dev and preview
 * servers bind to loopback only and trust no foreign Host headers. That is
 * the safe posture for a local application.
 *
 * For tunnels / sandboxed previews (like a demo over a proxy host) run:
 *
 *   GENOS_EXPOSE=lan npm run dev
 *
 * which binds 0.0.0.0 and accepts proxied hosts. This flag is a deliberate
 * demo convenience — never a production setting. The production build
 * (`npm run build`) is static output served by whatever hosts the desktop
 * shell; no permissive server configuration ships with it.
 */
const exposeLan = process.env.GENOS_EXPOSE === 'lan'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: exposeLan ? '0.0.0.0' : '127.0.0.1',
    port: 5178,
    strictPort: true,
    allowedHosts: exposeLan ? true : undefined,
  },
  preview: {
    // Previewing the production bundle stays strictly local.
    host: '127.0.0.1',
    port: 4178,
    strictPort: true,
  },
})
