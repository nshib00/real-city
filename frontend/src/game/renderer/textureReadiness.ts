type Entry = { status: 'loading' | 'loaded' | 'failed'; attempts: number; retryAt: number; requestedAt: number; listeners: Set<() => void> }

// Успешные текстуры принадлежат Pixi Assets. Этот класс не уничтожает GPU-ресурсы,
// пока ими могут пользоваться спрайты; он ограничивает повторы сетевой загрузки.
export class TextureReadiness {
  private entries = new Map<string, Entry>()
  constructor(private load: (url: string) => Promise<unknown>, private failed: () => void, private now = Date.now) {}
  ready(url: string, redraw: () => void) {
    const existing = this.entries.get(url)
    if (existing) existing.requestedAt = this.now()
    if (existing?.status === 'loaded') return true
    if (existing?.status === 'loading') { existing.listeners.add(redraw); return false }
    if (existing && (existing.attempts >= 3 || this.now() < existing.retryAt)) return false
    const entry: Entry = { status: 'loading', attempts: (existing?.attempts ?? 0) + 1, retryAt: 0, requestedAt: this.now(), listeners: new Set([redraw]) }
    this.entries.set(url, entry)
    void this.load(url).then(() => {
      entry.status = 'loaded'
      const listeners = [...entry.listeners]
      entry.listeners.clear()
      listeners.forEach((listener) => listener())
    }, () => {
      entry.status = 'failed'
      entry.retryAt = this.now() + 1000 * entry.attempts
      this.failed()
      const listeners = [...entry.listeners]
      entry.listeners.clear()
      listeners.forEach((listener) => listener())
    })
    return false
  }
  retryFailed() {
    // Явное действие пользователя запускает новый ограниченный цикл.
    for (const [url, entry] of this.entries) if (entry.status === 'failed') this.entries.delete(url)
  }
  diagnostics() {
    const states = [...this.entries.values()]
    return { loading: states.filter((entry) => entry.status === 'loading').length, failed: states.filter((entry) => entry.status === 'failed').length, retryable: states.filter((entry) => entry.status === 'failed' && entry.attempts < 3 && this.now() - entry.requestedAt < 5000).length, loaded: states.filter((entry) => entry.status === 'loaded').length }
  }
}
