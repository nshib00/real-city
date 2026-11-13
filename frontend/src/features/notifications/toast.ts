import { playUiSound } from '../../audio/playUiSound'

export type ToastSeverity = 'info' | 'warning' | 'error'
export type ToastDetail = { id: number; severity: ToastSeverity; message: string; player?: { name: string; level: number }; suffix?: string }

let nextId = 0
const eventName = 'real-city:toast'

export function showToast(severity: ToastSeverity, message: string, player?: ToastDetail['player'], suffix?: string): void {
  if (typeof window === 'undefined') return
  playUiSound(`ui.toast.${severity}`)
  window.dispatchEvent(new CustomEvent<ToastDetail>(eventName, { detail: { id: ++nextId, severity, message, player, suffix } }))
}

export function subscribeToasts(listener: (toast: ToastDetail) => void): () => void {
  const handler = (event: Event) => listener((event as CustomEvent<ToastDetail>).detail)
  window.addEventListener(eventName, handler)
  return () => window.removeEventListener(eventName, handler)
}
