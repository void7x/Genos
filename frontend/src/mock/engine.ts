/**
 * MOCK SERVICE IMPLEMENTATION.
 * ---------------------------------------------------------------------------
 * Everything in this file is DEMO ONLY.
 *
 *  - No file is read, written, listed or deleted.
 *  - No command, Git operation or test run is executed.
 *  - No AI inference happens; every Genos reply is a pre-written string from
 *    `src/mock/conversation.ts`.
 *
 * The class exists so the UI can be driven by a single stateful store that has
 * exactly the same surface the real backend service will have later. When the
 * integration happens, this file gets replaced (or bypassed) by
 * `createHttpBackedService()` in `src/services/transport.ts` and the components
 * do not change.
 *
 * Timings are deliberately slow enough to watch, fast enough to demo.
 */
import {
  mockFailingTests,
  mockProject,
  mockProjectTree,
} from './project'
import { mockGoal, mockHistory, mockMemories, mockTasks } from './context'
import {
  createEmptyWorkflow,
  mockPermissionTemplate,
  mockPlanSteps,
  mockRecoveryAutomatic,
  mockRecoveryManual,
  mockRollback,
  mockVerificationFail,
  mockVerificationPass,
  WORKFLOW_STAGES,
} from './workflow'
import { mockFailureOutput } from './files'
import {
  genosMessage,
  nextId,
  script,
  seedConversation,
  userMessage,
} from './conversation'
import {
  fail,
  okVoid,
  type ConnectionState,
  type ServiceResult,
} from '../services/types'
import type {
  ActionRecord,
  AgentStatus,
  ChatMessage,
  DemoScenario,
  GenosState,
  PlanStep,
  StepStatus,
  WorkflowPhaseStatus,
  WorkflowSnapshot,
  WorkflowStage,
} from '../types'

const cloneSteps = (): PlanStep[] => mockPlanSteps.map((s) => ({ ...s }))

const initialState = (): GenosState => ({
  project: { ...mockProject, gitState: { ...mockProject.gitState }, tests: { ...mockProject.tests } },
  status: 'idle',
  statusDetail: 'Ready',
  messages: seedConversation(),
  workflow: createEmptyWorkflow(),
  permission: null,
  verification: null,
  recovery: null,
  rollback: null,
  memories: [...mockMemories],
  tasks: mockTasks.map((t) => ({ ...t })),
  goal: { ...mockGoal },
  history: [...mockHistory],
  files: mockProjectTree.map((f) => ({ ...f })),
  notifications: [],
  busy: false,
})

export class MockGenosService {
  private state: GenosState = initialState()
  private listeners = new Set<() => void>()
  private timers: ReturnType<typeof setTimeout>[] = []
  private scenario: DemoScenario = 'success'
  private runSeq = 0
  /** The mock is synchronously available; mirrors the transport lifecycle. */
  private connection: ConnectionState = { status: 'ready' }

  getState = (): GenosState => this.state
  subscribe = (listener: () => void): (() => void) => { this.listeners.add(listener); return () => this.listeners.delete(listener) }
  private emit() { this.listeners.forEach((l) => l()) }
  private set(patch: Partial<GenosState>) { this.state = { ...this.state, ...patch }; this.emit() }
  private clearTimers() { this.timers.forEach(clearTimeout); this.timers = [] }
  private after(ms: number, fn: () => void) { const id = setTimeout(() => { this.timers = this.timers.filter((t) => t !== id); fn() }, ms); this.timers.push(id) }
  private status(status: AgentStatus, detail: string) { this.set({ status, statusDetail: detail }) }
  private push(message: ChatMessage) { this.set({ messages: [...this.state.messages, message] }) }
  private record(record: Omit<ActionRecord, 'id' | 'at'>) { const entry: ActionRecord = { ...record, id: nextId('act'), at: 'just now' }; this.set({ history: [entry, ...this.state.history] }) }
  private notify(tone: GenosState['notifications'][number]['tone'], title: string, body?: string) { const note = { id: nextId('ntf'), tone, title, body, at: new Date().toISOString() }; this.set({ notifications: [...this.state.notifications, note] }) }
  private patchWorkflow(patch: Partial<WorkflowSnapshot>) { this.set({ workflow: { ...this.state.workflow, ...patch } }) }
  private setStep(id: string, status: StepStatus, detail?: string) { const steps = this.state.workflow.steps.map((s) => s.id === id ? { ...s, status, detail: detail ?? s.detail } : s); const done = steps.filter((s) => s.status === 'completed').length; this.patchWorkflow({ steps, progress: steps.length ? done / steps.length : 0 }) }
  private setPhase(stage: WorkflowStage, status: WorkflowPhaseStatus) { this.patchWorkflow({ phase: stage, phases: this.state.workflow.phases.map((p) => (p.stage === stage ? { ...p, status } : p)) }) }

  init = async (): Promise<ServiceResult<void>> => okVoid()
  getConnectionState = (): ConnectionState => this.connection
  getProject = async () => this.state.project
  getGitStatus = async () => this.state.project.gitState
  getTestSummary = async () => this.state.project.tests
  getTasks = async () => this.state.tasks
  getGoal = async () => this.state.goal
  getMemories = async () => this.state.memories
  getWorkflow = async () => this.state.workflow
  getActionHistory = async () => this.state.history

  async sendMessage(text: string): Promise<ServiceResult<void>> {
    const trimmed = text.trim()
    if (!trimmed) return fail('invalid-request', 'Nothing to send.')
    if (this.state.busy) return fail('conflict', 'Genos is already working on a task.')
    this.push(userMessage(trimmed))
    const lower = trimmed.toLowerCase()
    const isFixFlow = /(fix|fail|test|resolver|duplicate|memory|improve)/.test(lower)
    const isGit = /(git|branch|commit|diff|clean)/.test(lower)
    const isMemoryWord = /(remember|memory|memories)/.test(lower) && !isFixFlow
    if (isGit) { this.status('thinking','Reading Git context'); this.after(700,()=>{this.push(genosMessage([{kind:'text',text:'Branch `main`, working tree clean, no unpushed commits.'},{kind:'command',command:'git status -sb',output:'## main...origin/main'}]));this.record({kind:'git',label:'Inspected Git status',detail:'main · clean',status:'ok'});this.status('idle','Ready')});return okVoid() }
    if (isMemoryWord) { this.status('thinking','Recalling project memory'); this.after(700,()=>{this.push(genosMessage([{kind:'text',text:'I hold 5 project memories. The two most relevant right now:'},{kind:'details',summary:'Resolver uses workspace-scoped memory',body:[{kind:'text',text:'Scopes are never merged across projects — `workspace_id` is always the first filter.'}]},{kind:'details',summary:'Rollback restores from the pre-edit snapshot',body:[{kind:'text',text:'Not from Git, so an uncommitted edit can still be reverted cleanly.'}]}]));this.status('idle','Ready')});return okVoid() }
    if (!isFixFlow) { this.status('thinking','Understanding request'); this.after(700,()=>{this.push(genosMessage([{kind:'text',text:'This prototype runs one scripted workflow end to end. Try: "Fix the failing tests in the memory resolver." — everything shown is mock data.'}]));this.status('idle','Ready')});return okVoid() }
    this.startFixWorkflow(); return okVoid()
  }

  async approveAction(): Promise<ServiceResult<void>> {
    const permission=this.state.permission;if(!permission||permission.state!=='pending')return fail('conflict','No approval is pending — the action was already handled.');this.set({permission:{...permission,state:'approved'},workflow:{...this.state.workflow,interrupted:false}});this.record({kind:'permission',label:'Approved edit',detail:permission.target,status:'ok'});this.notify('info','Approval recorded',permission.target);this.runExecution();return okVoid()
  }
  async denyAction(): Promise<ServiceResult<void>> {
    const permission=this.state.permission;if(!permission||permission.state!=='pending')return fail('conflict','No approval is pending — the action was already handled.');this.set({permission:{...permission,state:'denied'},busy:false});this.patchWorkflow({interrupted:true});this.setStep('step_2','blocked');this.setPhase('approval','done');this.status('idle','Paused — awaiting instruction');this.push(script.denied());this.record({kind:'permission',label:'Denied edit',detail:permission.target,status:'failed'});this.notify('info','Change not applied','Plan paused at step 2');return okVoid()
  }

  async resumeWorkflow(): Promise<ServiceResult<void>> { if(!this.state.workflow.interrupted)return fail('conflict','No interrupted workflow to resume.');const run=this.runSeq;this.patchWorkflow({interrupted:false});this.set({busy:true});this.status('working','Resuming workflow');this.push(genosMessage([{kind:'text',text:'Resuming the paused workflow from the approval step. Nothing executed while it was paused.'}]));this.after(900,()=>{if(run!==this.runSeq)return;this.set({permission:{...mockPermissionTemplate,id:nextId('perm'),state:'pending',createdAt:new Date().toISOString()}});this.setPhase('approval','active');this.setStep('step_2','waiting');this.status('waiting','Needs approval');this.notify('warning','Genos needs your approval','Edit app/memory/resolver.py')});return okVoid() }
  async retryWorkflow(): Promise<ServiceResult<void>> { if(this.state.workflow.steps.length===0)return fail('invalid-request','There is no workflow to retry.');this.reset();await this.sendMessage('Fix the failing tests in the memory resolver.');return okVoid() }
  async requestRollback(): Promise<ServiceResult<void>> { if(!this.state.verification||this.state.verification.passed)return fail('conflict','There is no failed verification to roll back.');this.set({recovery:null,status:'working',statusDetail:'Rolling back'});this.after(1100,()=>{this.set({rollback:{...mockRollback},status:'success',statusDetail:'Rolled back'});this.setStep('step_4','completed','State restored · verification re-run');this.setPhase('complete','done');this.patchWorkflow({progress:1});this.push(script.rolledBack());this.record({kind:'rollback',label:'Rolled back failed edit',detail:mockRollback.target,status:'undone'});this.notify('warning','Change rolled back',mockRollback.target);this.set({project:{...this.state.project,tests:{...mockProject.tests},gitState:{...mockProject.gitState}},files:mockProjectTree.map((f)=>({...f}))})});return okVoid() }
  setDemoScenario(scenario:DemoScenario){if(this.scenario===scenario)return;this.scenario=scenario;this.reset()}
  getDemoScenario():DemoScenario{return this.scenario}
  reset(){this.clearTimers();this.runSeq+=1;this.set({...initialState(),notifications:[]})}
  dismissNotification(id:string){this.set({notifications:this.state.notifications.filter((n)=>n.id!==id)})}
  private startFixWorkflow(){this.clearTimers();this.runSeq+=1;const run=this.runSeq;this.set({busy:true,workflow:{...createEmptyWorkflow(),phases:WORKFLOW_STAGES.map((s)=>({...s,status:s.stage==='plan'?('active' as WorkflowPhaseStatus):('pending' as WorkflowPhaseStatus)}))},verification:null,recovery:null,rollback:null,permission:null});this.status('thinking','Understanding request');this.push(script.understanding());this.after(900,()=>{if(run!==this.runSeq)return;this.push(script.context());this.record({kind:'inspect',label:'Inspected project',detail:'412 files · Python',status:'ok'});this.status('working','Analyzing implementation')});this.after(1900,()=>{if(run!==this.runSeq)return;this.patchWorkflow({steps:cloneSteps()});this.push(script.plan());this.setPhase('plan','done');this.status('working','Preparing change');this.record({kind:'task',label:'Created task',detail:'Improve memory resolver',status:'ok'})});this.after(2800,()=>{if(run!==this.runSeq)return;this.set({permission:{...mockPermissionTemplate,id:nextId('perm'),state:'pending',createdAt:new Date().toISOString()}});this.setPhase('approval','active');this.setStep('step_2','waiting');this.status('waiting','Needs approval');this.notify('warning','Genos needs your approval','Edit app/memory/resolver.py')})}
  private runExecution(){const run=this.runSeq;this.set({busy:true});this.setPhase('approval','done');this.setPhase('execute','active');this.status('working','Applying change');this.push(script.approved());this.setStep('step_1','running');this.after(900,()=>{if(run!==this.runSeq)return;this.setStep('step_1','completed');this.setStep('step_2','running')});this.after(2100,()=>{if(run!==this.runSeq)return;this.setStep('step_2','completed');this.set({project:{...this.state.project,gitState:{...this.state.project.gitState,clean:false,modifiedFiles:2}},files:this.state.files.map((f)=>f.path==='app/memory/resolver.py'||f.path==='tests/memory/test_resolver.py'?{...f,change:'modified' as const}:f)});this.record({kind:'edit',label:'Updated resolver.py',detail:'app/memory/resolver.py · +3 −2',status:'ok'});this.reportAppliedChanges();this.setStep('step_3','running');this.status('working','Running test suite')});if(this.scenario==='success')this.runSuccess(run);else this.runFailure(run)}
  private runSuccess(run:number){this.after(3800,()=>{if(run!==this.runSeq)return;this.setStep('step_3','completed','282 passed, 4 skipped in 12.40s');this.record({kind:'test',label:'Ran test suite',detail:'pytest -q · 282 passed',status:'ok'});this.setPhase('execute','done');this.setPhase('verify','active');this.setStep('step_4','running');this.status('working','Verifying result')});this.after(5000,()=>{if(run!==this.runSeq)return;this.set({verification:mockVerificationPass});this.setStep('step_4','completed');this.patchWorkflow({progress:1});this.setPhase('verify','done');this.setPhase('complete','done');this.push(script.success());this.set({busy:false,tasks:this.state.tasks.map((t)=>t.id==='task_1'?{...t,state:'done' as const}:t),goal:{...this.state.goal,progress:.91}});this.status('success','Task completed');this.notify('success','Workflow completed','Verification passed · 4 checks')})}
  private runFailure(run:number){this.after(3600,()=>{if(run!==this.runSeq)return;this.setStep('step_3','failed','3 failed, 279 passed in 12.90s');this.record({kind:'test',label:'Ran test suite',detail:'pytest -q · 3 failed',status:'failed'});this.setPhase('execute','failed');this.setPhase('verify','failed');this.setStep('step_4','failed','Verification stopped after test failure');this.set({verification:{...mockVerificationFail,failure:{...mockVerificationFail.failure!,output:mockFailureOutput}},recovery:{...mockRecoveryAutomatic},project:{...this.state.project,tests:{...mockFailingTests}}});this.status('error','Verification failed');this.push(script.failed());this.notify('error','Verification failed','3 tests failed in tests/memory')});this.after(5600,()=>{if(run!==this.runSeq)return;this.set({recovery:{...mockRecoveryAutomatic,attempt:2}});this.notify('info','Retrying test suite','Attempt 2 of 2')});this.after(7400,()=>{if(run!==this.runSeq)return;this.set({recovery:{...mockRecoveryManual}});this.status('waiting','Needs your attention');this.notify('warning','Recovery needs your attention','Retry produced the same failure')})}
  private reportAppliedChanges(){this.push(genosMessage([{kind:'text',text:'Change applied under a pre-edit snapshot. Two files touched:'},{kind:'fileList',files:[{path:'app/memory/resolver.py',change:'modified'},{path:'tests/memory/test_resolver.py',change:'modified'}]}]))}
}
