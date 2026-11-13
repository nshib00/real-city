import { getAudioSettings, onAudioSettings } from './audioSettings'

let player: HTMLAudioElement | null = null
const playlist = [
  '/assets/audio/music/sunset-walk.mp3',
  '/assets/audio/music/meadow-thoughts.mp3',
  '/assets/audio/music/feel-good-ambient.mp3',
  '/assets/audio/music/exploration-theme.mp3',
]
let trackIndex = 0

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
    player = new Audio(playlist[trackIndex])
    player.preload = 'none'
    player.addEventListener('ended', () => {
      trackIndex = (trackIndex + 1) % playlist.length
      if (!player) return
      player.src = playlist[trackIndex]
      syncMusic()
    })
    onAudioSettings(syncMusic)
  }
  syncMusic()
}

export function updateMusicVisibility(): void {
  if (!player) return
  if (document.hidden) player.pause()
  else startMusic()
}
