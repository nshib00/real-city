import type { SoundBus } from './soundEvents'

export type AudioSettings = {
  version: 1
  muted: boolean
  master: number
  ui: number
  world: number
  alerts: number
  ambience: number
  music: number
  chat: boolean
  reduced: boolean
}

export const defaultAudioSettings: AudioSettings = {
  version: 1, muted: false, master: 0.8, ui: 0.65,
  world: 0.8, alerts: 0.85, ambience: 0.35, music: 0.35, chat: true, reduced: false,
}

const key = 'real-city.audio.settings.v1'
let current: AudioSettings | undefined
const listeners = new Set<(settings: AudioSettings) => void>()

function unit(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : fallback
}

export function getAudioSettings(): AudioSettings {
  if (current) return current
  let saved: Partial<AudioSettings> = {}
  try {
    const raw = localStorage.getItem(key)
    if (raw) saved = JSON.parse(raw) as Partial<AudioSettings>
    else saved = {
      muted: localStorage.getItem('real-city.audio.muted') === 'true',
      chat: localStorage.getItem('real-city.audio.chat-enabled') !== 'false',
    }
  } catch { /* Без localStorage настройки живут до перезагрузки. */ }
  current = {
    version: 1,
    muted: typeof saved.muted === 'boolean' ? saved.muted : defaultAudioSettings.muted,
    master: unit(saved.master, defaultAudioSettings.master),
    ui: unit(saved.ui, defaultAudioSettings.ui),
    world: unit(saved.world, defaultAudioSettings.world),
    alerts: unit(saved.alerts, defaultAudioSettings.alerts),
    ambience: unit(saved.ambience, defaultAudioSettings.ambience),
    music: unit(saved.music, defaultAudioSettings.music),
    chat: typeof saved.chat === 'boolean' ? saved.chat : defaultAudioSettings.chat,
    reduced: typeof saved.reduced === 'boolean' ? saved.reduced : defaultAudioSettings.reduced,
  }
  return current
}

export function updateAudioSettings(patch: Partial<Omit<AudioSettings, 'version'>>): AudioSettings {
  const before = getAudioSettings()
  current = {
    ...before, ...patch, version: 1,
    master: unit(patch.master, before.master), ui: unit(patch.ui, before.ui),
    world: unit(patch.world, before.world), alerts: unit(patch.alerts, before.alerts),
    ambience: unit(patch.ambience, before.ambience),
    music: unit(patch.music, before.music),
  }
  try { localStorage.setItem(key, JSON.stringify(current)) } catch { /* Настройки остаются в памяти. */ }
  for (const listener of listeners) listener(current)
  return current
}

export function onAudioSettings(listener: (settings: AudioSettings) => void): () => void {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export function busVolume(bus: SoundBus, settings = getAudioSettings()): number {
  return settings.muted ? 0 : settings.master * settings[bus]
}
