import { useId, useState, type ReactElement } from 'react'
import { cloneElement } from 'react'

// Передавать один фокусируемый элемент. Недоступную кнопку объясняет соседний текст.
export function Tooltip({ text, children }: { text: string; children: ReactElement<{ 'aria-describedby'?: string }> }) {
  const id = useId()
  const [dismissed, setDismissed] = useState(false)
  return <span className="ui-tooltip-anchor" onMouseEnter={() => setDismissed(false)} onFocus={() => setDismissed(false)} onKeyDown={(event) => { if (event.key === 'Escape') { setDismissed(true); event.stopPropagation() } }}>
    {cloneElement(children, { 'aria-describedby': [children.props['aria-describedby'], id].filter(Boolean).join(' ') })}
    <span id={id} role="tooltip" className="ui-tooltip" data-dismissed={dismissed}>{text}</span>
  </span>
}
