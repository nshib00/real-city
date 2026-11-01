import type { ButtonHTMLAttributes } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean; variant?: 'primary' | 'secondary' | 'danger' }

export function Button({ loading = false, disabled, variant = 'secondary', children, className = '', ...props }: ButtonProps) {
  return <button {...props} type={props.type ?? 'button'} className={`ui-button ui-button-${variant} ${className}`} disabled={disabled || loading} aria-busy={loading || undefined}>
    {loading && <span aria-hidden="true">… </span>}{children}
  </button>
}
