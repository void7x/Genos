import { Button, Card, Icon } from '../components/ui'
import { Details } from '../components/ui/Details'
import { CodeBlock } from '../components/code/CodeBlock'
import type { VerificationResult } from '../types'

interface VerificationCardProps {
  result: VerificationResult
  onInspectFailure?: () => void
}

/** Verification is what connects execution to evidence. */
export function VerificationCard({ result, onInspectFailure }: VerificationCardProps) {
  const passed = result.passed

  return (
    <Card
      title={passed ? 'Verification' : 'Verification failed'}
      icon={passed ? 'check' : 'alert'}
      tone={passed ? 'ok' : 'err'}
      live="polite"
    >
      <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {result.checks.map((check) => (
          <li className="check" data-status={check.status} key={check.id}>
            <span className="check__icon">
              <Icon
                name={
                  check.status === 'passed'
                    ? 'check'
                    : check.status === 'failed'
                      ? 'x'
                      : check.status === 'skipped'
                        ? 'circle'
                        : 'clock'
                }
                size={12}
              />
            </span>
            <span className="check__label">{check.label}</span>
            {check.detail ? <span className="check__detail">{check.detail}</span> : null}
          </li>
        ))}
      </ul>

      {!passed && result.failure ? (
        <div style={{ marginTop: 8, borderTop: '1px solid var(--g-border)', paddingTop: 8 }}>
          <div className="notice__title" style={{ color: '#f0b0b0' }}>
            {result.failure.failedCount} tests failed
          </div>
          <p className="notice__detail" style={{ marginTop: 3 }}>
            <span className="g-mono">{result.failure.title}</span>
            <br />
            {result.failure.detail}
          </p>
          <div className="notice__actions">
            <Button size="sm" icon="eye" onClick={onInspectFailure}>
              View failure
            </Button>
          </div>
          <div style={{ marginTop: 8 }}>
            <Details summary="Failure output">
              <CodeBlock code={result.failure.output} language="text" variant="output" />
            </Details>
          </div>
        </div>
      ) : null}
    </Card>
  )
}
