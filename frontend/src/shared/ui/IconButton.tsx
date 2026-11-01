import type { ComponentType } from 'react'
import type { AeolianIconProps } from './AeolianIcon'
import { AeolianIcon } from './AeolianIcon'
import { playUiSound } from '../../audio/playUiSound'
import type { SoundId } from '../../audio/soundEvents'

type IconButtonProps = {
  label: string
  icon: ComponentType<Omit<AeolianIconProps, 'name'>>
  active?: boolean
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  sound?: SoundId
  shortcut?: string
}

export function IconButton({ label, icon: Icon, active = false, disabled = false, loading = false, onClick, sound = 'ui.click', shortcut }: IconButtonProps) {
  return (
    <button
      className={active ? 'icon-button icon-button-active' : 'icon-button'}
      type="button"
      title={shortcut ? `${label} (${shortcut})` : label}
      aria-keyshortcuts={shortcut}
      aria-label={label}
      aria-pressed={active}
      aria-busy={loading || undefined}
      data-audio-handled="true"
      disabled={disabled || loading}
      onClick={() => { playUiSound(sound); onClick?.() }}
    >
      {loading ? <AeolianIcon name="clock" size={20} /> : <Icon size={20} aria-hidden="true" />}
    </button>
  )
}
