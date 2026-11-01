import { describe, expect, it, vi } from 'vitest'
import { ClientTelemetry, installClientTelemetry } from './clientTelemetry'

describe('client telemetry', () => {
  it('captures browser failures without forwarding messages or asset URLs and removes listeners', async () => {
    vi.useFakeTimers()
    const batches: unknown[] = []
    const receive = (event: Event) => batches.push((event as CustomEvent).detail)
    window.addEventListener('real-city:client-telemetry', receive)
    const stop = installClientTelemetry()
    try {
      window.dispatchEvent(new ErrorEvent('error', { message: 'token=private player=secret', filename: 'https://private.invalid/?token=private' }))
      const image = document.createElement('img')
      document.body.append(image)
      image.dispatchEvent(new Event('error'))
      image.remove()
      await vi.advanceTimersByTimeAsync(30_000)
      const serialized = JSON.stringify(batches)
      expect(serialized).toContain('runtime_error')
      expect(serialized).toContain('asset_error')
      expect(serialized).not.toContain('private')
      expect(serialized).not.toContain('secret')
      stop()
      window.dispatchEvent(new ErrorEvent('error'))
      await vi.advanceTimersByTimeAsync(60_000)
      expect(batches).toHaveLength(1)
    } finally {
      stop()
      window.removeEventListener('real-city:client-telemetry', receive)
      vi.useRealTimers()
    }
  })
  it('deduplicates, sends only fixed fields and bounds an offline backlog', async () => {
    let now = 0
    const receive = vi.fn()
    const telemetry = new ClientTelemetry(receive, 'test', () => now)
    for (let i = 0; i < 100; i++) {
      telemetry.record('asset_error'); telemetry.record('asset_error'); now += 60_000
    }
    await telemetry.flush(false)
    expect(receive).not.toHaveBeenCalled()
    await telemetry.flush()
    expect(receive.mock.calls[0][0]).toHaveLength(32)
    expect(receive.mock.calls[0][0][0]).toEqual({ schema: 1, version: 'test', signal: 'asset_error', minute: 68 })
  })

  it('does not retry recursively and clears a failed in-flight batch on account change', async () => {
    let fail!: (reason?: unknown) => void
    const receive = vi.fn(() => new Promise<void>((_, reject) => { fail = reject }))
    const telemetry = new ClientTelemetry(receive, 'test')
    telemetry.record('runtime_error')
    const pending = telemetry.flush()
    await telemetry.flush()
    telemetry.reset()
    fail(new Error('private token and URL must never be recorded'))
    await pending
    await telemetry.flush()
    expect(receive).toHaveBeenCalledTimes(1)
  })

  it('retries a failed batch only on the next explicit flush', async () => {
    const receive = vi.fn().mockRejectedValueOnce(new Error()).mockResolvedValue(undefined)
    const telemetry = new ClientTelemetry(receive, 'test')
    telemetry.record('ws_gap')
    await telemetry.flush()
    expect(receive).toHaveBeenCalledTimes(1)
    await telemetry.flush()
    expect(receive).toHaveBeenCalledTimes(2)
  })
})
