import { afterEach, describe, expect, it } from 'vitest'
import { busVolume, defaultAudioSettings, updateAudioSettings } from './audioSettings'

describe('настройки звука', () => {
  afterEach(() => updateAudioSettings(defaultAudioSettings))

  it('сохраняет версию, громкость и mute и ограничивает значения ползунков', () => {
    const settings = updateAudioSettings({ master: 0.4, world: 2, muted: true, chat: false })
    expect(settings).toMatchObject({ version: 1, master: 0.4, world: 1, muted: true, chat: false })
    expect(busVolume('world')).toBe(0)
    expect(JSON.parse(localStorage.getItem('real-city.audio.settings.v1')!)).toMatchObject(settings)
    updateAudioSettings({ muted: false })
    expect(busVolume('world')).toBe(0.4)
  })
})
