import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

import { playUiSound } from '../../audio/playUiSound'
import { IconButton } from './IconButton'

type ModalProps = {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
  className?: string
}

export function Modal({ title, open, onClose, children, className }: ModalProps) {
  const wasOpen = useRef(false)
  useEffect(() => {
    if (open && !wasOpen.current) playUiSound('ui.dialog.open')
    wasOpen.current = open
  }, [open])
  if (!open) {
    return null
  }

  return (
    <div className={className ? `modal-backdrop ${className}` : 'modal-backdrop'} role="presentation" onClick={onClose}>
      <section className="modal-panel" role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <h2>{title}</h2>
          <IconButton label="Закрыть" icon={X} sound="ui.cancel" onClick={onClose} />
        </header>
        {children}
      </section>
    </div>
  )
}
