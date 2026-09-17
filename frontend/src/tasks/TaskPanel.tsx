import { Card, Icon, ProgressBar } from '../components/ui'
import { percent } from '../utils/format'
import type { Goal, TaskItem } from '../types'

export function TaskPanel({ tasks, goal }: { tasks: TaskItem[]; goal: Goal }) {
  return (
    <Card title="Tasks" icon="target" actions={<span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-label)' }}>{tasks.filter((t) => t.state === 'done').length}/{tasks.length}</span>}>
      <ul className="list" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {tasks.map((task) => (
          <li className="list-row" data-state={task.state} key={task.id}>
            <span className="task-dot" data-state={task.state} aria-hidden="true" />
            <span className="list-row__title">{task.title}</span>
            <span className="list-row__meta">{task.state === 'done' ? 'done' : task.state === 'active' ? 'active' : 'todo'}</span>
          </li>
        ))}
      </ul>
      <div style={{ marginTop: 9, borderTop: '1px solid var(--g-border)', paddingTop: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
          <Icon name="target" size={12} style={{ color: 'var(--g-accent-2)' }} />
          <span className="g-label">Goal</span>
        </div>
        <div style={{ fontSize: 'var(--g-fs-sm)', color: 'var(--g-text-2)' }}>{goal.title}</div>
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <ProgressBar value={goal.progress} size="lg" label={`Goal progress: ${percent(goal.progress)}`} />
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="g-mono g-dim" style={{ fontSize: 'var(--g-fs-label)' }}>{goal.detail}</span>
            <span className="g-mono" style={{ fontSize: 'var(--g-fs-label)', color: 'var(--g-text-2)' }}>{percent(goal.progress)}</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export function GoalStrip({ goal }: { goal: Goal }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span className="g-label">Goal</span>
        <span className="g-mono" style={{ fontSize: 'var(--g-fs-label)', color: 'var(--g-text-2)' }}>{percent(goal.progress)}</span>
      </div>
      <div style={{ fontSize: 'var(--g-fs-sm)', color: 'var(--g-text-2)', marginBottom: 6 }}>{goal.title}</div>
      <ProgressBar value={goal.progress} label="Goal progress" />
    </div>
  )
}
