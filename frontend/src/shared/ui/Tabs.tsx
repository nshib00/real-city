import type { ReactNode } from 'react'
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
  return (
    <div className="tabs">
      <div className="tab-list" role="tablist">
        {items.map((item) => (
          <button
            className={item.id === active ? 'tab-button tab-button-active' : 'tab-button'}
            key={item.id}
            type="button"
            role="tab"
            aria-selected={item.id === active}
            data-audio-handled="true"
            onClick={() => { if (item.id !== active) { playUiSound('ui.tab'); onChange(item.id) } }}
          >
            <span>{item.label}</span>
            {item.badge ? <strong>{item.badge}</strong> : null}
          </button>
        ))}
      </div>
      <div className="tab-panel" role="tabpanel">
        {children}
      </div>
    </div>
  )
}
