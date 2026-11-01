/** Bounded replay window; TTL is checked on reads, including low traffic sessions. */
export class AudioEventWindow {
  private seen = new Map<string, number>()
  constructor(private capacity: number, private ttl: number, private now = Date.now) {}

  accept(id: string): boolean {
    const now = this.now()
    for (const [key, at] of this.seen) {
      if (now - at < this.ttl) break
      this.seen.delete(key)
    }
    if (this.seen.has(id)) return false
    this.seen.set(id, now)
    while (this.seen.size > this.capacity) this.seen.delete(this.seen.keys().next().value!)
    return true
  }
}
