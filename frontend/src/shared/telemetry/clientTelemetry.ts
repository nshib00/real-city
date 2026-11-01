import { version } from '../../../package.json'

export type ClientSignal = 'runtime_error' | 'unhandled_rejection' | 'asset_error' | 'render_error' | 'ws_reconnecting' | 'ws_recovered' | 'ws_gap'
export type ClientReport = { schema: 1; version: string; signal: ClientSignal; minute: number }
type Receiver = (reports: readonly ClientReport[]) => void | Promise<void>

/** Only fixed signals leave the client: never exception text, URLs, IDs or coordinates. */
export class ClientTelemetry {
  private queue: ClientReport[] = []
  private seen = new Set<ClientSignal>()
  private minute = -1
  private sending = false
  private generation = 0

  constructor(private receiver: Receiver, private version: string, private now = Date.now) {}

  record(signal: ClientSignal) {
    const minute = Math.floor(this.now() / 60_000)
    if (minute !== this.minute) { this.minute = minute; this.seen.clear() }
    if (this.seen.has(signal)) return
    this.seen.add(signal)
    this.queue.push({ schema: 1, version: this.version, signal, minute })
    if (this.queue.length > 32) this.queue.shift()
  }

  reset() { this.generation++; this.queue = []; this.seen.clear() }

  async flush(online = true) {
    if (!online || this.sending || !this.queue.length) return
    const batch = this.queue.splice(0)
    const generation = this.generation
    this.sending = true
    try { await this.receiver(batch) }
    catch {
      // No recursive reporting, immediate retry or cross-account requeue.
      if (generation === this.generation) this.queue = [...batch, ...this.queue].slice(-32)
    } finally { this.sending = false }
  }
}

// Local diagnostics receiver. External collection requires a deployed, authenticated sink.
export const clientTelemetry = new ClientTelemetry((reports) => {
  window.dispatchEvent(new CustomEvent('real-city:client-telemetry', { detail: reports }))
}, version)

export function installClientTelemetry() {
  const error = (event: Event) => clientTelemetry.record(event.target instanceof Element ? 'asset_error' : 'runtime_error')
  const rejection = () => clientTelemetry.record('unhandled_rejection')
  const flush = () => { void clientTelemetry.flush(navigator.onLine) }
  window.addEventListener('error', error, true)
  window.addEventListener('unhandledrejection', rejection)
  window.addEventListener('online', flush)
  const timer = window.setInterval(flush, 30_000)
  return () => {
    window.removeEventListener('error', error, true)
    window.removeEventListener('unhandledrejection', rejection)
    window.removeEventListener('online', flush)
    window.clearInterval(timer)
    clientTelemetry.reset()
  }
}
