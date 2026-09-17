# GENOS · Frontend Prototype (integration-ready)

A **frontend-only** prototype of GENOS — a local-first project engineering
assistant that behaves like a persistent desktop companion: a small draggable
bubble above your work, expandable into a compact assistant panel and further
into a floating workspace.

The prototype demonstrates the complete interaction surface of a coding agent
— plan → approval → execution → verification → recovery/rollback — while
remaining a pure presentation layer. **Nothing is executed, no files are touched, no Git command runs, no AI inference happens.** All behaviour comes from a mock service behind the same contract a real backend will implement.

> Visual language: deep charcoal surfaces, restrained violet accents,
> structured task presentation — an original GENOS identity.

---

## 1 · What this is

- React 18 + TypeScript + Vite presentation layer.
- Floating companion with three surfaces: **bubble**, **compact panel**,
  **expanded workspace** (all draggable, viewport-clamped).
- A typed **service contract** (`GenosService`) with an async **connection
  lifecycle** and a **typed result/error model**.
- A **mock implementation** of that contract for demos and tests.
- A **transport adapter** (`createHttpBackedService`) that turns any
  backend transport into the contract — the single integration seam.
- A Vitest test suite covering shell, workflow, permission, transport and
  drag behaviour.

## 2 · What this is NOT

| Not | Why |
| --- | --- |
| A backend / agent runtime | The existing Python Genos backend owns agent logic |
| A permission system | Approval UI only; the backend decides |
| An executor / test runner / Git client | UI shows states; the backend produces them |
| A shell/control authority | The frontend can *request* known operations (closed command union); it can never name arbitrary backend commands or shell text |
| A finished desktop app | Browser prototype; see §15 for the desktop-shell path |

## 3 · Install

Requires **Node 18+** (developed against Node 20). No environment variables,
keys, tokens or credentials are needed or used.

```bash
npm ci
```

## 4 · Run

```bash
npm run dev        # http://127.0.0.1:5178  (loopback only — see §security)
```

Tunnel / sandbox preview (deliberate, non-production convenience):

```bash
GENOS_EXPOSE=lan npm run dev   # binds 0.0.0.0 and accepts proxied hosts
```

## 5 · Lint

```bash
npm run lint
```

## 6 · Build

```bash
npm run build      # tsc -b (strict) + vite build → dist/
npm run preview    # serves dist/ on 127.0.0.1:4178 only
```

## 7 · Test

```bash
npm test           # vitest run (jsdom + Testing Library)
```

Coverage highlights (`src/test/`):

- `app.test.tsx` — bubble renders/opens; compact expands & collapses; composer
  input + Enter; Approve/Deny call the service; **Resume ≠ Retry** in the UI.
- `transport.test.ts` — initialization lifecycle (fetch/push race), typed
  errors, closed command mapping, retry after failure.
- `service-contract.test.ts` — demo controls isolated; resume/retry/guard
  semantics with typed results.
- `components.test.tsx` — workflow step states, permission accessibility,
  verification failure, recovery, connection screens.
- `useDraggable.test.ts` — clamping, mode-change re-clamping, click-vs-drag.

## 8 · Floating UI modes

| Mode | Surface | Notes |
| --- | --- | --- |
| `bubble` | 54px draggable control | six states: idle/thinking/working/waiting/success/error (icon+badge+aria, never colour-only) |
| `compact` | 376×≤600 panel | status strip, blocking approval first, current task, activity, composer |
| `expanded` | 960×≤680 workspace | context rail · conversation · activity rail (tabs) |

Keys: `Mod+J` open/close · `Mod+Shift+J` expand · `Esc` collapse ·
`Enter` send · `Shift+Enter` newline. Dragging works on bubble and title bar;
a drag never counts as a click; positions stay inside the available area and
re-clamp on mode change and viewport resize.

## 9 · Service architecture

```
React components
      │  useGenosState / useGenosConnection / handlers
      ▼
  GenosService            ← the ONLY data entry point (src/services)
      ├──────────────────────────┐
      ▼                          ▼
MockGenosService          createHttpBackedService(transport)
(src/mock/engine.ts)             │
                                 ▼
                          GenosTransport  → existing Python backend
```

- `src/services/types.ts` — contract: lifecycle, reads, writes, result model.
- `src/services/genosService.ts` — the singleton; swap point for integration.
- `src/services/demo.ts` — demo-only controls, structurally detected, used by
  demo UI that renders conditionally (§10).
- Components never import `src/mock/**`, never touch filesystem/subprocess/Git.

## 10 · Mock architecture

All fake values and the scripted orchestration live in `src/mock/`:

- `engine.ts` — `MockGenosService` (state machine, timers, typed results).
- `project/context/workflow/files/conversation.ts` — demo domain values.

`MockGenosService` additionally implements `DemoControls`
(`setDemoScenario/getDemoScenario/reset`). The singleton is typed only as
`GenosService`; `getDemoControls(service)` returns the extras when present and
`null` otherwise — the demo footer renders only in the former case. A
production service needs **none** of these methods.

## 11 · Real backend integration point

```ts
// src/services/genosService.ts — the only line that changes:
import { createHttpBackedService } from './transport'
import { realGenosTransport } from './realTransport' // provided at integration
export const genosService: GenosService = createHttpBackedService(realGenosTransport)
```

Implement `GenosTransport` (`fetchState`, `onState`, `command`) over HTTP /
WebSocket / IPC. `command` accepts only the closed `GenosCommand` union
(`sendMessage | approveAction | denyAction | resumeWorkflow | retryWorkflow |
requestRollback | dismissNotification`). Raise `GenosTransportError(code, …)`
for typed backend failures. **No component changes.**

## 12 · Transport lifecycle

`init()` (idempotent, called by the shell effect and the Retry button):

1. connection → `connecting`; **subscribe first** so no push is missed;
2. fetch the initial snapshot;
3. a push arriving during the fetch marks `ready` immediately and the late
   fetch result is discarded (never overwrites newer state);
4. fetch success fills the cache only if nothing arrived yet → `ready`;
5. fetch failure with no snapshot → `error` with a typed `ServiceError`;
6. `getState()` is only read by the UI after `ready` (the shell gates on
   `useGenosConnection`, rendering `ConnectionScreen` otherwise).

## 13 · Error model

Every mutation answers `ServiceResult<void>`:

```ts
{ ok: true, value } | { ok: false, error: { code, message } }
```

Codes: `permission-denied · invalid-request · backend-unavailable · conflict ·
timeout · unknown`. The UI shows failures as a dismissible, announced notice
(`ActionErrorToast`) and never crashes; the backend remains authoritative for
what each code means in context (stale approval ⇒ `conflict`, etc.).

## 14 · Resume vs retry

| Situation (backend-authoritative) | Flag in snapshot | UI action |
| --- | --- | --- |
| Workflow paused mid-flight (denied approval, interrupted session) | `workflow.interrupted: true` | **Resume workflow** — continues from persisted state |
| Workflow failed verification | phase `failed` | **Retry workflow** — restart per retry semantics |

The two are separate contract methods (`resumeWorkflow`, `retryWorkflow`);
the UI shows exactly one of them, and the mock demonstrates both paths.

## 15 · Future desktop-shell integration

Presentation state (`view`, `mode`, position) is isolated in
`src/hooks/useFloatingWindow.ts` and is entirely separate from backend state.
A real shell (Tauri/Electron/PySide webview) can take it over:

- `view`/`mode` → webview size & visibility,
- `position` → native window placement,
- `useDraggable` → native title-bar dragging,
- `DesktopStage` (decorative scenery, `src/layout/desktopScene.ts`) is removed
  outright; it is stage-prop content, not domain data, and nothing else
  references it.

The hook only clamps inside *whatever area the shell provides* — no assumption
that the browser viewport equals a desktop window manager.

## 16 · Security boundary

- **Hosts:** dev and preview bind loopback by default and trust no foreign
  Host header. `GENOS_EXPOSE=lan` is an opt-in demo convenience for tunnels;
  the production build is static output with no permissive server config.
- **Commands:** closed typed union only; the frontend cannot request arbitrary
  commands, cannot pass shell text, and performs no permission logic — the
  Python backend re-validates everything and remains the only authority for
  permissions, filesystem, process execution, Git, verification, rollback and
  workflow state.
- **Secrets:** none exist, none are required, none are read from the
  environment.

## Accessibility

Semantic controls with ARIA labels; tooltips on icon-only buttons; visible
`:focus-visible` rings; conversation as `role="log"`; status + notifications
announced via `aria-live`/`role="status|alert"`; critical states always
icon+text, never colour-only; `prefers-reduced-motion` honoured.

## Structure

```
src/
  App.tsx               connection gate + floating shell wiring
  types/                domain types (incl. workflow.interrupted)
  services/             contract · singleton · transport · demo isolation
  mock/                 demo values + scripted MockGenosService
  hooks/                useGenosState · useGenosConnection · useFloatingWindow
                        · useDraggable · useKeyboardShortcuts · …
  layout/               bubble · window · header · toasts · connection screens
                        · DesktopStage (+ desktopScene scenery)
  panels/               CompactPanel · ExpandedWorkspace · context panels
  workflow/             steps · stages · permission · verification · recovery
                        · rollback
  chat/ memory/ tasks/ git/  domain panels
  components/           ui primitives · code/diff display
  styles/               tokens + component CSS (dark theme)
  test/                 vitest suite + setup
```
