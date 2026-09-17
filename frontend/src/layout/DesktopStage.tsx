import { GenosMark, Icon } from '../components/ui'

import { SCENE_CODE, SCENE_FILES, SCENE_META, SCENE_TITLE } from './desktopScene'

/**
 * Stand-in desktop.
 *
 * The prototype has no real desktop shell, so this renders a dimmed editor
 * behind the floating window. It exists to communicate the core UX principle:
 * the developer's IDE stays primary, Genos floats beside it.
 */
export function DesktopStage({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="desktop" aria-hidden="false">
      <div className="desktop__grid" aria-hidden="true" />

      <div className="ide" aria-hidden="true">
        <div className="ide__bar">
          <span className="ide__dots">
            <i />
            <i />
            <i />
          </span>
          <span className="ide__title">{SCENE_TITLE}</span>
          <span className="ide__title" style={{ marginLeft: 'auto' }}>
            {SCENE_META}
          </span>
        </div>
        <div className="ide__body">
          <div className="ide__files">
            {SCENE_FILES.map((f, i) => (
              <span key={f} data-active={i === 3}>
                {f}
              </span>
            ))}
          </div>
          <div className="ide__code">
            {SCENE_CODE.map((line, i) => (
              <div key={i}>
                <b>{i + 1}</b>
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="desktop__dock">
        <GenosMark size={15} />
        <span>Genos floats above your workspace</span>
        <button type="button" className="dock__btn" onClick={onOpen}>
          <Icon name="plus" size={12} />
          Open Genos
        </button>
        <span className="dock__hint">Mod+J</span>
      </div>
    </div>
  )
}
