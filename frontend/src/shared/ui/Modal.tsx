import type { ReactNode } from 'react'
import { X } from 'lucide-react'

import { IconButton } from './IconButton'

type ModalProps = {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

export function Modal({ title, open, onClose, children }: ModalProps) {
  if (!open) {
    return null
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section className="modal-panel" role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <h2>{title}</h2>
          <IconButton label="Закрыть" icon={X} onClick={onClose} />
        </header>
        {children}
      </section>
    </div>
  )
}
