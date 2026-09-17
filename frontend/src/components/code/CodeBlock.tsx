import { Icon } from '../ui/Icon'
import { TOKEN_CLASS, tokenizeLine } from '../../utils/highlight'

interface CodeBlockProps {
  code: string
  language?: string
  filename?: string
  /** Renders a small "output" label instead of a language tag. */
  variant?: 'code' | 'output'
}

/** Read-only code / command output preview. Never editable, never executed. */
export function CodeBlock({ code, language = 'python', filename, variant = 'code' }: CodeBlockProps) {
  const lines = code.replace(/\n$/, '').split('\n')

  return (
    <figure className="code" style={{ margin: 0 }}>
      <figcaption className="code__head">
        {variant === 'output' ? <Icon name="terminal" size={11} /> : <Icon name="file" size={11} />}
        <span>{filename ?? (variant === 'output' ? 'output' : language)}</span>
        <span className="code__lang">{variant === 'output' ? 'stdout' : language}</span>
      </figcaption>
      <pre className="code__body">
        <code>
          {lines.map((line, i) => (
            <span key={i}>
              {tokenizeLine(line, language).map((tok, j) => {
                const cls = TOKEN_CLASS[tok.type]
                return cls ? (
                  <span key={j} className={cls}>
                    {tok.value}
                  </span>
                ) : (
                  <span key={j}>{tok.value}</span>
                )
              })}
              {'\n'}
            </span>
          ))}
        </code>
      </pre>
    </figure>
  )
}
