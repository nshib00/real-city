import { AudioGraph } from './audioGraph'
import { getAudioSettings, onAudioSettings } from './audioSettings'
import { soundCatalog } from './soundCatalog'
import type { SoundId } from './soundEvents'

type Voice = { source: AudioBufferSourceNode; gain: GainNode; id: SoundId; level: number }
type Loop = { source: AudioBufferSourceNode; gain: GainNode; stopTimer?: number }
const priorityValue = { low: 0, normal: 1, high: 2, critical: 3 } as const
export type AudioDiagnostics = { state: AudioContextState | 'uninitialized'; voices: number; cacheBytes: number; lastSound: SoundId | null; limited: number; errors: string[] }

export class AudioManager {
  private graph: AudioGraph | null = null
  private cache = new Map<string, AudioBuffer>()
  private loading = new Map<string, Promise<AudioBuffer>>()
  private failed = new Map<string, number>()
  private voices = new Set<Voice>()
  private loops = new Map<SoundId, Loop>()
  private loopTargets = new Map<SoundId, number>()
  private lastPlayed = new Map<SoundId, number>()
  private variants = new Map<SoundId, number>()
  private gestureSeen = false
  private hidden = false
  private cacheLimit = 16 * 1024 * 1024
  private lastSound: SoundId | null = null
  private limited = 0
  private errors: string[] = []

  constructor() {
    onAudioSettings((settings) => {
      this.graph?.setSettings(settings)
      if (this.hidden) this.graph?.suspendForHidden(true)
    })
  }

  async unlock(): Promise<boolean> {
    if (typeof window === 'undefined' || typeof window.AudioContext === 'undefined') return false
    this.gestureSeen = true
    if (!this.graph) this.graph = new AudioGraph(new window.AudioContext())
    try {
      if (this.graph.context.state !== 'running') await this.graph.context.resume()
      if (this.graph.context.state !== 'running') throw new Error('AudioContext остаётся заблокированным')
      this.graph.suspendForHidden(this.hidden)
      return true
    } catch (error) {
      this.recordError(`audio.context_blocked: ${String(error)}`)
      return false
    }
  }

  setHidden(hidden: boolean): void {
    this.hidden = hidden
    this.graph?.suspendForHidden(hidden)
    if (hidden) for (const voice of [...this.voices]) this.stopVoice(voice)
    if (hidden) for (const id of [...this.loops.keys()]) this.stopLoop(id)
    else if (this.gestureSeen) void this.unlock()
  }

  async preload(id: SoundId): Promise<void> {
    if (!this.graph || this.graph.context.state !== 'running') return
    const url = soundCatalog[id].variants[0]
    if (url) try { await this.load(url) } catch { /* Отсутствующий preload не мешает игре. */ }
  }

  setLoop(id: SoundId, level: number): void {
    const definition = soundCatalog[id]
    if (definition.bus !== 'ambience') return
    const target = Math.max(0, Math.min(1, level))
    this.loopTargets.set(id, target)
    const current = this.loops.get(id)
    if (current) {
      if (current.stopTimer !== undefined) window.clearTimeout(current.stopTimer)
      current.gain.gain.setTargetAtTime(target * definition.volume, this.graph!.context.currentTime, 0.18)
      if (target === 0) current.stopTimer = window.setTimeout(() => this.stopLoop(id), 650)
      return
    }
    if (!target || !this.graph || this.graph.context.state !== 'running' || this.hidden) return
    const url = definition.variants[0]
    if (!url) return
    void this.load(url).then((buffer) => {
      if (!this.graph || this.hidden || !this.loopTargets.get(id) || this.loops.has(id)) return
      const context = this.graph.context
      const source = context.createBufferSource()
      const gain = context.createGain()
      source.buffer = buffer
      source.loop = true
      gain.gain.value = 0
      source.connect(gain)
      gain.connect(this.graph.buses.ambience)
      this.loops.set(id, { source, gain })
      gain.gain.setTargetAtTime((this.loopTargets.get(id) ?? 0) * definition.volume, context.currentTime, 0.18)
      source.start()
    }).catch((error) => this.recordError(`audio.decode_failed ${id}: ${String(error)}`))
  }

  play(id: SoundId, options: { gain?: number; pan?: number; variantIndex?: number } = {}): boolean {
    const definition = soundCatalog[id]
    if (!definition?.variants.length || !this.gestureSeen || !this.graph || this.hidden || getAudioSettings().muted) return false
    if (this.graph.context.state !== 'running') {
      void this.unlock().then((ready) => { if (ready) this.play(id, options) })
      return true
    }
    const now = performance.now()
    if (now - (this.lastPlayed.get(id) ?? -Infinity) < definition.cooldownMs) return false
    const same = [...this.voices].filter((voice) => voice.id === id)
    const limit = getAudioSettings().reduced ? Math.min(1, definition.voiceLimit) : definition.voiceLimit
    if (same.length >= limit) {
      const quietest = same.reduce((a, b) => a.level < b.level ? a : b)
      if (quietest.level >= (options.gain ?? 1)) { this.limited++; return false }
      this.stopVoice(quietest)
    }
    const index = options.variantIndex ?? (this.variants.get(id) ?? 0)
    this.variants.set(id, (index + 1) % definition.variants.length)
    const firstIndex = Math.max(0, Math.min(definition.variants.length - 1, index))
    this.lastPlayed.set(id, now)
    this.lastSound = id
    void this.loadVariant(definition.variants, firstIndex).then((buffer) => {
      if (!this.graph || this.hidden || getAudioSettings().muted || this.graph.context.state !== 'running') return
      const activeForId = [...this.voices].filter((voice) => voice.id === id)
      if (activeForId.length >= limit) {
        const quietest = activeForId.reduce((a, b) => a.level < b.level ? a : b)
        if (quietest.level >= (options.gain ?? 1)) { this.limited++; return }
        this.stopVoice(quietest)
      }
      const maximum = getAudioSettings().reduced ? 5 : 12
      if (this.voices.size >= maximum) {
        const quietest = [...this.voices].reduce((a, b) => {
          const scoreA = priorityValue[soundCatalog[a.id].priority] * 2 + a.level
          const scoreB = priorityValue[soundCatalog[b.id].priority] * 2 + b.level
          return scoreA < scoreB ? a : b
        })
        const incoming = priorityValue[definition.priority] * 2 + (options.gain ?? 1)
        const existing = priorityValue[soundCatalog[quietest.id].priority] * 2 + quietest.level
        if (incoming <= existing) { this.limited++; return }
        this.stopVoice(quietest)
      }
      const context = this.graph.context
      const source = context.createBufferSource()
      const gain = context.createGain()
      source.buffer = buffer
      gain.gain.value = definition.volume * Math.max(0, Math.min(1, options.gain ?? 1))
      source.connect(gain)
      if (definition.spatial && options.pan !== undefined && typeof context.createStereoPanner === 'function') {
        const panner = context.createStereoPanner()
        panner.pan.value = Math.max(-1, Math.min(1, options.pan))
        gain.connect(panner)
        panner.connect(this.graph.buses[definition.bus])
      } else gain.connect(this.graph.buses[definition.bus])
      const voice = { source, gain, id, level: options.gain ?? 1 }
      source.onended = () => { this.voices.delete(voice); source.disconnect(); gain.disconnect() }
      this.voices.add(voice)
      source.start()
    }).catch((error) => this.recordError(`audio.decode_failed ${id}: ${String(error)}`))
    return true
  }

  diagnostics(): AudioDiagnostics {
    return { state: this.graph?.context.state ?? 'uninitialized', voices: this.voices.size + this.loops.size,
      cacheBytes: [...this.cache.values()].reduce((sum, buffer) => sum + buffer.length * buffer.numberOfChannels * 4, 0),
      lastSound: this.lastSound, limited: this.limited, errors: [...this.errors] }
  }

  private stopVoice(voice: Voice): void {
    try { voice.source.stop() } catch { /* Источник уже завершён. */ }
    this.voices.delete(voice)
  }

  private stopLoop(id: SoundId): void {
    const loop = this.loops.get(id)
    if (!loop) return
    if (loop.stopTimer !== undefined) window.clearTimeout(loop.stopTimer)
    try { loop.source.stop() } catch { /* Петля уже завершена. */ }
    loop.source.disconnect()
    loop.gain.disconnect()
    this.loops.delete(id)
  }

  private async load(url: string): Promise<AudioBuffer> {
    if (Date.now() - (this.failed.get(url) ?? -Infinity) < 30_000) throw new Error('asset_missing')
    const cached = this.cache.get(url)
    if (cached) { this.cache.delete(url); this.cache.set(url, cached); return cached }
    const pending = this.loading.get(url)
    if (pending) return pending
    const task = (async () => {
      const response = await fetch(url)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const buffer = await this.graph!.context.decodeAudioData(await response.arrayBuffer())
      this.cache.set(url, buffer)
      while (this.diagnostics().cacheBytes > this.cacheLimit && this.cache.size > 1) this.cache.delete(this.cache.keys().next().value!)
      return buffer
    })()
    this.loading.set(url, task)
    try { return await task } catch (error) { this.failed.set(url, Date.now()); throw error } finally { this.loading.delete(url) }
  }

  private async loadVariant(variants: readonly string[], first: number): Promise<AudioBuffer> {
    let lastError: unknown
    for (let offset = 0; offset < variants.length; offset++) {
      try { return await this.load(variants[(first + offset) % variants.length]) }
      catch (error) { lastError = error }
    }
    throw lastError
  }

  private recordError(message: string): void {
    if (this.errors.at(-1) === message) return
    this.errors.push(message)
    if (this.errors.length > 10) this.errors.shift()
    if (import.meta.env.DEV) console.warn(message)
  }
}

export const audioManager = new AudioManager()
