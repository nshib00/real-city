import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

import { playUiSound } from '../../audio/playUiSound'
import { IconButton } from './IconButton'

type DrawerProps = {
  title: string
  open: boolean
  side?: 'left' | 'right'
  onClose: () => void
  children: ReactNode
}

export function Drawer({ title, open, side = 'right', onClose, children }: DrawerProps) {
  const wasOpen = useRef(open)
  useEffect(() => {
    if (open && !wasOpen.current) playUiSound('ui.panel.open')
    wasOpen.current = open
  }, [open])
  return (
    <aside className={open ? `drawer drawer-${side} drawer-open` : `drawer drawer-${side}`} aria-label={title} aria-hidden={!open}>
      <header className="drawer-header">
        <h2>{title}</h2>
        <IconButton label="Закрыть" icon={X} sound="ui.panel.close" onClick={onClose} />
      </header>
      {children}
    </aside>
  )
}
