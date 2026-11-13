import { useEffect, useState } from 'react'

import { subscribeToasts, type ToastDetail } from './toast'
import { LevelEmblem } from '../player/LevelEmblem'

export function ToastCenter() {
  const [toasts, setToasts] = useState<ToastDetail[]>([])

  useEffect(() => {
    const timeouts = new Set<number>()
    const unsubscribe = subscribeToasts((toast) => {
      setToasts((current) => [...current.slice(-3), toast])
      const timeout = window.setTimeout(() => {
        setToasts((current) => current.filter((item) => item.id !== toast.id))
        timeouts.delete(timeout)
      }, 5000)
      timeouts.add(timeout)
    })
    return () => { unsubscribe(); for (const timeout of timeouts) window.clearTimeout(timeout) }
  }, [])

  return <div className="audio-toast-stack">
    {toasts.map((toast) => <div className={`audio-toast audio-toast-${toast.severity}`} role={toast.severity === 'error' ? 'alert' : 'status'} key={toast.id}>{toast.message}{toast.player ? <> <LevelEmblem level={toast.player.level} size="small" /> {toast.player.name}</> : null}{toast.suffix}</div>)}
  </div>
}
