/**
 * Mock: workflow, plan, permission, verification, recovery and rollback
 * templates used by the demo orchestration in `src/mock/engine.ts`.
 *
 * DEMO DATA ONLY. No file is touched, no command is executed.
 */
import type { PermissionRequest, PlanStep, RecoveryState, RollbackState, VerificationResult, WorkflowStage, WorkflowSnapshot } from '../types'
import { mockFailureOutput, mockResolverDiff } from './files'
export const WORKFLOW_NAME='Fix failing memory resolver tests'
export const mockPlanSteps:PlanStep[]=[
{id:'step_1',index:1,title:'Inspect relevant files',status:'pending',detail:'3 files matched: resolver, manager, resolver tests'},
{id:'step_2',index:2,title:'Update resolver de-duplication',status:'pending',detail:'app/memory/resolver.py · resolve_memories()',command:'edit app/memory/resolver.py'},
{id:'step_3',index:3,title:'Run test suite',status:'pending',detail:'Scoped to tests/memory + tests/verification',command:'pytest -q tests/memory tests/verification'},
{id:'step_4',index:4,title:'Verify result',status:'pending',detail:'Syntax check · diff inspection · diagnostics'}]
export const WORKFLOW_STAGES:{stage:WorkflowStage;label:string}[]=[{stage:'plan',label:'Plan'},{stage:'approval',label:'Approval'},{stage:'execute',label:'Execute'},{stage:'verify',label:'Verify'},{stage:'complete',label:'Complete'}]
export function createEmptyWorkflow():WorkflowSnapshot{return{id:'wf_demo',name:WORKFLOW_NAME,phase:'plan',phases:WORKFLOW_STAGES.map(s=>({...s,status:'pending' as const})),steps:[],progress:0,persistable:true,resumable:true,interrupted:false}}
export const mockPermissionTemplate:Omit<PermissionRequest,'id'|'createdAt'|'state'>={operation:'edit-file',target:'app/memory/resolver.py',reason:'Remove duplicate memory entries before ranking so the resolver returns a unique, workspace-scoped result set.',risk:'medium',diff:mockResolverDiff}
export const mockVerificationPass:VerificationResult={id:'ver_pass',passed:true,summary:'Verification complete · 4 checks passed',checks:[{id:'chk_1',label:'File updated',status:'passed',detail:'app/memory/resolver.py · +3 −2'},{id:'chk_2',label:'Syntax valid',status:'passed',detail:'ast parse clean · ruff: no findings'},{id:'chk_3',label:'Tests passed',status:'passed',detail:'282 passed, 4 skipped in 12.40s'},{id:'chk_4',label:'Git diff inspected',status:'passed',detail:'2 files · no unrelated changes'}]}
export const mockVerificationFail:VerificationResult={id:'ver_fail',passed:false,summary:'3 tests failed after the change',checks:[{id:'chk_1',label:'File updated',status:'passed',detail:'app/memory/resolver.py · +3 −2'},{id:'chk_2',label:'Syntax valid',status:'passed',detail:'ast parse clean'},{id:'chk_3',label:'Tests passed',status:'failed',detail:'3 failed, 279 passed in 12.90s'},{id:'chk_4',label:'Git diff inspected',status:'skipped',detail:'Skipped after test failure'}],failure:{title:'test_resolver_returns_unique_memories',detail:'assert 4 == 2 — the de-duplication key collapses distinct scopes.',failedCount:3,output:mockFailureOutput}}
export const mockRecoveryAutomatic:RecoveryState={active:true,title:'Test execution failed',detail:'Genos detected a recoverable failure and is retrying the test command.',automatic:true,attempt:1}
export const mockRecoveryManual:RecoveryState={active:true,title:'Recovery requires your attention',detail:'The retry produced the same failure. The de-duplication key needs a scope component before Genos can continue.',automatic:false,attempt:2}
export const mockRollback:RollbackState={active:true,target:'app/memory/resolver.py',detail:'The change failed verification, so Genos restored the previous file state from the pre-edit snapshot.',restored:true}
