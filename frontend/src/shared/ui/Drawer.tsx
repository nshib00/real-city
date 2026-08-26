import type { ReactNode } from 'react'
import { X } from 'lucide-react'

import { IconButton } from './IconButton'

type DrawerProps = {
  title: string
  open: boolean
  side?: 'left' | 'right'
  onClose: () => void
  children: ReactNode
}

export function Drawer({ title, open, side = 'right', onClose, children }: DrawerProps) {
  return (
    <aside className={open ? `drawer drawer-${side} drawer-open` : `drawer drawer-${side}`} aria-label={title} aria-hidden={!open}>
      <header className="drawer-header">
        <h2>{title}</h2>
        <IconButton label="Закрыть" icon={X} onClick={onClose} />
      </header>
      {children}
    </aside>
  )
}
