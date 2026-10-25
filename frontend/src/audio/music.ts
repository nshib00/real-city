import { getAudioSettings, onAudioSettings } from './audioSettings'

let player: HTMLAudioElement | null = null

function syncMusic(): void {
  if (!player) return
  const settings = getAudioSettings()
  player.volume = settings.muted ? 0 : settings.master * settings.music * 0.55
  if (settings.muted || settings.music === 0 || document.hidden) player.pause()
  else if (player.paused) void player.play().catch(() => undefined)
}

export function startMusic(): void {
  if (typeof Audio === 'undefined') return
  if (!player) {
    player = new Audio('/assets/audio/music/sunset-walk.mp3')
    player.loop = true
    player.preload = 'none'
    onAudioSettings(syncMusic)
  }
  syncMusic()
}

export function updateMusicVisibility(): void {
  if (!player) return
  if (document.hidden) player.pause()
  else startMusic()
}
