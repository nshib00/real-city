import type { ComponentType } from 'react'
import type { LucideProps } from 'lucide-react'
import { playUiSound } from '../../audio/playUiSound'
import type { SoundId } from '../../audio/soundEvents'

type IconButtonProps = {
  label: string
  icon: ComponentType<LucideProps>
  active?: boolean
  disabled?: boolean
  onClick?: () => void
  sound?: SoundId
}

export function IconButton({ label, icon: Icon, active = false, disabled = false, onClick, sound = 'ui.click' }: IconButtonProps) {
  return (
    <button
      className={active ? 'icon-button icon-button-active' : 'icon-button'}
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      data-audio-handled="true"
      disabled={disabled}
      onClick={() => { playUiSound(sound); onClick?.() }}
    >
      <Icon size={20} aria-hidden="true" />
    </button>
  )
}
