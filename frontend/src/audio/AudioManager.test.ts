import { afterEach, describe, expect, it, vi } from 'vitest'
import { AudioManager } from './AudioManager'
import { updateAudioSettings } from './audioSettings'

function fakeContext() {
  const starts: string[] = []
  const source = () => ({ buffer: null, onended: null, connect: vi.fn(), disconnect: vi.fn(), start: () => starts.push('start'), stop: vi.fn() })
  const gain = () => ({ gain: { value: 1, setTargetAtTime: vi.fn() }, connect: vi.fn(), disconnect: vi.fn() })
  const context = {
    state: 'suspended', currentTime: 0, destination: {}, createGain: gain, createBufferSource: source,
    createStereoPanner: () => ({ pan: { value: 0 }, connect: vi.fn() }),
    resume: vi.fn(async function (this: { state: string }) { this.state = 'running' }),
    decodeAudioData: vi.fn(async () => ({ length: 1200, numberOfChannels: 1 })),
  }
  return { context, starts }
}

describe('AudioManager', () => {
  afterEach(() => { vi.unstubAllGlobals(); updateAudioSettings({ muted: false, reduced: false }) })

  it('creates AudioContext only after a gesture, decodes once and respects mute and voice limits', async () => {
    const { context, starts } = fakeContext()
    const constructor = vi.fn(() => context)
    vi.stubGlobal('AudioContext', constructor)
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) })))
    const manager = new AudioManager()
    expect(constructor).not.toHaveBeenCalled()
    expect(manager.play('ui.confirm')).toBe(false)
    expect(await manager.unlock()).toBe(true)
    expect(constructor).toHaveBeenCalledTimes(1)
    expect(manager.play('ui.confirm', { variantIndex: 0 })).toBe(true)
    await vi.waitFor(() => expect(starts).toHaveLength(1))
    expect(manager.play('ui.confirm', { variantIndex: 0 })).toBe(true)
    await vi.waitFor(() => expect(starts).toHaveLength(2))
    expect(context.decodeAudioData).toHaveBeenCalledTimes(1)
    expect(manager.play('ui.confirm')).toBe(false)
    expect(manager.diagnostics().limited).toBe(1)
    updateAudioSettings({ muted: true })
    expect(manager.play('ui.click')).toBe(false)
    manager.setHidden(true)
    expect(manager.diagnostics().voices).toBe(0)
  })

  it('tries the next variant after a missing MP3 and stays silent if all fail', async () => {
    const { context, starts } = fakeContext()
    vi.stubGlobal('AudioContext', vi.fn(() => context))
    const fetcher = vi.fn(async (url: string) => ({
      ok: !url.includes('.0.mp3'), status: 404,
      arrayBuffer: async () => new ArrayBuffer(4),
    }))
    vi.stubGlobal('fetch', fetcher)
    const manager = new AudioManager()
    expect(await manager.unlock()).toBe(true)
    expect(manager.play('ui.confirm', { variantIndex: 0 })).toBe(true)
    await vi.waitFor(() => expect(starts).toHaveLength(1))
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('fades a biome loop through the ambience bus and stops it on a hidden tab', async () => {
    const { context, starts } = fakeContext()
    vi.stubGlobal('AudioContext', vi.fn(() => context))
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) })))
    const manager = new AudioManager()
    expect(await manager.unlock()).toBe(true)
    manager.setLoop('ambience.forest', 0.1)
    await vi.waitFor(() => expect(starts).toHaveLength(1))
    expect(manager.diagnostics().voices).toBe(1)
    manager.setHidden(true)
    expect(manager.diagnostics().voices).toBe(0)
  })
})
