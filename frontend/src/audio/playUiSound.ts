import type { SoundId } from './soundEvents'
import { audioManager } from './AudioManager'
import { getAudioSettings, updateAudioSettings } from './audioSettings'

export function preloadUiSounds(): void {
  // Декодирование начинается после первого жеста в AudioProvider.
}

export function isUiSoundMuted(): boolean {
  return getAudioSettings().muted
}

export function setUiSoundMuted(muted: boolean): void {
  updateAudioSettings({ muted })
}

export function playUiSound(id: SoundId, variantIndex?: number, volumeScale = 1): void {
  audioManager.play(id, { variantIndex, gain: volumeScale })
}
