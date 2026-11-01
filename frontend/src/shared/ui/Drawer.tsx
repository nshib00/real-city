import { useEffect, useRef, type ReactNode } from 'react'
import { X } from './icons'

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
  const panel = useRef<HTMLElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    panel.current?.focus({ preventScroll: true })
    return () => { if (previous?.isConnected) previous.focus({ preventScroll: true }) }
  }, [open])
  useEffect(() => {
    if (open && !wasOpen.current) playUiSound('ui.panel.open')
    wasOpen.current = open
  }, [open])
  return (
    <aside ref={panel} tabIndex={-1} onKeyDown={(event) => { if (event.key === 'Escape') { event.stopPropagation(); close.current() } }} className={open ? `drawer drawer-${side} drawer-open` : `drawer drawer-${side}`} aria-label={title} aria-hidden={!open} inert={!open}>
      <header className="drawer-header">
        <h2>{title}</h2>
        <IconButton label="Закрыть" icon={X} sound="ui.panel.close" onClick={onClose} />
      </header>
      {children}
    </aside>
  )
}
