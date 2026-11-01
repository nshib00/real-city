import type { ReactNode } from 'react'

type Props = {
  loaded: number
  total: number
  message: string
  busy?: boolean
  hint?: string
  children?: ReactNode
}

export function LoadingScreenView({ loaded, total, message, busy = true, hint, children }: Props) {
  const percent = total ? Math.floor(loaded / total * 100) : 0
  return <main className="initial-loading-screen" aria-label="Загрузка игры" aria-busy={busy}>
    <div className="initial-loading-content">
      <h1 className="initial-loading-logo">Эолия</h1>
      <div className="initial-loading-progress-row">
        <div className="initial-loading-bar" role="progressbar" aria-label="Загрузка файлов игры" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
          <span style={{ width: `${percent}%` }} />
        </div>
        <strong className="initial-loading-percent" aria-hidden="true">{percent}%</strong>
      </div>
      <div className="initial-loading-details">
        <span role="status" aria-live="polite">{message}</span>
        <span>{loaded} / {total} файлов</span>
      </div>
      {hint ? <p className="initial-loading-hint">{hint}</p> : null}
      {children}
    </div>
  </main>
}
