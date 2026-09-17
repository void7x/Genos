import type { ReactNode } from 'react'
import { CodeBlock } from '../components/code/CodeBlock'
import { FileChip } from '../components/code/FileChip'
import { Details, GenosMark, ThinkingDots } from '../components/ui'
import { clockTime } from '../utils/format'
import type { ChatMessage as ChatMessageModel, MessageBlock } from '../types'

/** Renders `backticked` spans as inline code inside Genos prose. */
function renderInline(text: string): ReactNode[] {
  return text.split(/(`[^`]+`)/g).map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code className="inline" key={i}>
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={i}>{part}</span>
  })
}

function Block({ block }: { block: MessageBlock }) {
  switch (block.kind) {
    case 'text':
      return <p style={{ margin: 0 }}>{renderInline(block.text)}</p>
    case 'code':
      return <CodeBlock code={block.code} language={block.language} filename={block.filename} />
    case 'command':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <CodeBlock code={block.command} language="bash" variant="output" filename={block.command} />
          {block.output ? <CodeBlock code={block.output} language="text" variant="output" /> : null}
        </div>
      )
    case 'fileList':
      return (
        <div className="msg__files">
          {block.files.map((f) => (
            <FileChip key={f.path} file={f} />
          ))}
        </div>
      )
    case 'details':
      return (
        <Details summary={block.summary}>
          <div className="msg__blocks">
            {block.body.map((b, i) => (
              <Block key={i} block={b} />
            ))}
          </div>
        </Details>
      )
    default:
      return null
  }
}

/** One conversation turn. */
export function Message({ message }: { message: ChatMessageModel }) {
  const isUser = message.role === 'user'

  return (
    <article className={`msg msg--${message.role}`}>
      <header className="msg__who">
        {!isUser ? <GenosMark size={11} /> : null}
        <span>{isUser ? 'You' : 'Genos'}</span>
        <span className="g-dim">·</span>
        <time dateTime={message.at} className="g-dim g-mono">
          {clockTime(message.at)}
        </time>
      </header>

      <div className="msg__bubble">
        <div className="msg__blocks">
          {message.blocks.map((block, i) => (
            <Block key={i} block={block} />
          ))}
        </div>
      </div>

      {message.note ? (
        <span className="msg__note">
          {!isUser ? <ThinkingDots label={message.note} /> : null}
          {message.note}
        </span>
      ) : null}
    </article>
  )
}
