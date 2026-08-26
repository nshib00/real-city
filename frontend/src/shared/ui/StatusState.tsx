type StatusStateProps = {
  title?: string
  variant?: 'empty' | 'loading' | 'error' | 'offline'
  action?: {
    label: string
    onClick: () => void
  }
  children: string
}

export function StatusState({ title, variant = 'empty', action, children }: StatusStateProps) {
  return (
    <div className={`status-state status-state-${variant}`} role={variant === 'error' ? 'alert' : 'status'}>
      {title ? <h2>{title}</h2> : null}
      <p>{children}</p>
      {action ? (
        <button type="button" onClick={action.onClick}>
          {action.label}
        </button>
      ) : null}
    </div>
  )
}
