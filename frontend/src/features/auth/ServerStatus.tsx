import { useEffect, useState } from 'react'

export function ServerStatus() {
  const [status, setStatus] = useState('Проверяем доступность мира…')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let disposed = false
    const timeout = window.setTimeout(() => controller.abort(), 8000)
    fetch('/ready', { signal: controller.signal, cache: 'no-store' })
      .then(async response => {
        const data = await response.json() as { status?: string }
        if (!response.ok || data.status !== 'ready') throw new Error('unavailable')
        if (!disposed) setStatus('Мир доступен')
      }).catch(() => { if (!disposed) setStatus('Не удалось проверить доступность мира') })
    return () => { disposed = true; clearTimeout(timeout); controller.abort() }
  }, [attempt])
  return <div className="start-server"><span role="status">{status}</span>{status.startsWith('Не удалось') ? <button type="button" onClick={() => { setStatus('Проверяем доступность мира…'); setAttempt(attempt + 1) }}>Проверить снова</button> : null}</div>
}
