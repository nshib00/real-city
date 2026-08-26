import type { ComponentType } from 'react'
import type { LucideProps } from 'lucide-react'

type IconButtonProps = {
  label: string
  icon: ComponentType<LucideProps>
  active?: boolean
  disabled?: boolean
  onClick?: () => void
}

export function IconButton({ label, icon: Icon, active = false, disabled = false, onClick }: IconButtonProps) {
  return (
    <button
      className={active ? 'icon-button icon-button-active' : 'icon-button'}
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon size={20} aria-hidden="true" />
    </button>
  )
}
