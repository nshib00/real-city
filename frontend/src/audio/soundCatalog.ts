import { soundEvents, soundEventOverrides, type SoundBus, type SoundId, type SoundPriority } from './soundEvents'
import { soundManifest } from './soundManifest'

export type SoundDefinition = {
  id: SoundId
  version: 1
  variants: readonly string[]
  bus: SoundBus
  volume: number
  voiceLimit: number
  cooldownMs: number
  spatial: boolean
  priority: SoundPriority
  preload: boolean
}

const catalog = {} as Record<SoundId, SoundDefinition>
for (const family of Object.values(soundEvents)) {
  for (const id of family.ids) {
    const bus = soundEventOverrides[id]?.bus ?? family.bus
    catalog[id] = {
      id, version: 1, variants: soundManifest[id] ?? [], bus,
      volume: bus === 'ambience' ? 0.2 : bus === 'alerts' ? 0.6 : bus === 'ui' ? 0.36 : 0.5,
      voiceLimit: bus === 'ambience' ? 4 : bus === 'world' ? 3 : 2,
      cooldownMs: id === 'ui.click' ? 70 : bus === 'world' ? 100 : 0,
      spatial: bus === 'world',
      priority: soundEventOverrides[id]?.priority ?? family.priority,
      preload: id === 'ui.click',
    }
  }
}

export const soundCatalog: Readonly<Record<SoundId, SoundDefinition>> = catalog
