import { useId, type ReactNode } from 'react'
import { playUiSound } from '../../audio/playUiSound'

type TabItem<T extends string> = {
  id: T
  label: string
  badge?: number
}

type TabsProps<T extends string> = {
  items: readonly TabItem<T>[]
  active: T
  onChange: (active: T) => void
  children: ReactNode
}

export function Tabs<T extends string>({ items, active, onChange, children }: TabsProps<T>) {
  const prefix = useId()
  return (
    <div className="tabs">
      <div className="tab-list" role="tablist">
        {items.map((item) => (
          <button
            className={item.id === active ? 'tab-button tab-button-active' : 'tab-button'}
            key={item.id}
            type="button"
            role="tab"
            id={`${prefix}-${item.id}`}
            aria-controls={`${prefix}-panel`}
            tabIndex={item.id === active ? 0 : -1}
            onKeyDown={(event) => {
              const index = items.indexOf(item)
              const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : event.key === 'ArrowRight' ? (index + 1) % items.length : event.key === 'ArrowLeft' ? (index - 1 + items.length) % items.length : -1
              if (next < 0) return
              event.preventDefault()
              onChange(items[next].id)
              document.getElementById(`${prefix}-${items[next].id}`)?.focus()
            }}
            aria-selected={item.id === active}
            data-audio-handled="true"
            onClick={() => { if (item.id !== active) { playUiSound('ui.tab'); onChange(item.id) } }}
          >
            <span>{item.label}</span>
            {item.badge ? <strong>{item.badge}</strong> : null}
          </button>
        ))}
      </div>
      <div className="tab-panel" role="tabpanel" id={`${prefix}-panel`} aria-labelledby={`${prefix}-${active}`} tabIndex={0}>
        {children}
      </div>
    </div>
  )
}
