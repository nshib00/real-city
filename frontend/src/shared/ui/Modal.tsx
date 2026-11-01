import { useEffect, useRef, type ReactNode } from 'react'
import { X } from './icons'

import { playUiSound } from '../../audio/playUiSound'
import { IconButton } from './IconButton'

const modalStack: symbol[] = []

type ModalProps = {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
  className?: string
}

export function Modal({ title, open, onClose, children, className }: ModalProps) {
  const wasOpen = useRef(false)
  const panel = useRef<HTMLElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    const id = Symbol()
    modalStack.push(id)
    const focusable = () => Array.from(panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]') ?? []).filter((node) => {
      if (node.closest('[hidden], [inert], [aria-hidden="true"]')) return false
      for (let current: HTMLElement | null = node; current; current = current.parentElement) {
        const style = getComputedStyle(current)
        if (style.display === 'none' || style.visibility === 'hidden') return false
        if (current === panel.current) break
      }
      return true
    })
    ;(focusable()[0] ?? panel.current)?.focus()
    function keydown(event: KeyboardEvent) {
      if (modalStack[modalStack.length - 1] !== id) return
      if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        close.current()
      }
      if (event.key !== 'Tab') return
      const nodes = focusable()
      const first = nodes[0]
      const last = nodes[nodes.length - 1]
      if (!first) { event.preventDefault(); panel.current?.focus(); return }
      if (event.shiftKey && (document.activeElement === first || !panel.current?.contains(document.activeElement))) {
        event.preventDefault(); last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || !panel.current?.contains(document.activeElement))) {
        event.preventDefault(); first.focus()
      }
    }
    document.addEventListener('keydown', keydown, true)
    return () => {
      modalStack.splice(modalStack.indexOf(id), 1)
      document.removeEventListener('keydown', keydown, true)
      if (previous?.isConnected) previous.focus()
    }
  }, [open])
  useEffect(() => {
    if (open && !wasOpen.current) playUiSound('ui.dialog.open')
    wasOpen.current = open
  }, [open])
  if (!open) {
    return null
  }

  return (
    <div className={className ? `modal-backdrop ${className}` : 'modal-backdrop'} role="presentation" onClick={onClose}>
      <section ref={panel} tabIndex={-1} className="modal-panel" role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <h2>{title}</h2>
          <IconButton label="Закрыть" icon={X} sound="ui.cancel" onClick={onClose} />
        </header>
        {children}
      </section>
    </div>
  )
}
