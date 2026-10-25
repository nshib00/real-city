import type { SoundBus } from './soundEvents'
import { getAudioSettings, type AudioSettings } from './audioSettings'

export class AudioGraph {
  readonly context: AudioContext
  readonly master: GainNode
  readonly buses: Record<SoundBus, GainNode>

  constructor(context: AudioContext) {
    this.context = context
    this.master = context.createGain()
    this.master.connect(context.destination)
    this.buses = {
      ui: context.createGain(), world: context.createGain(),
      alerts: context.createGain(), ambience: context.createGain(),
    }
    for (const bus of Object.values(this.buses)) bus.connect(this.master)
    this.setSettings(getAudioSettings())
  }

  setSettings(settings: AudioSettings): void {
    this.master.gain.value = settings.muted ? 0 : settings.master
    for (const name of Object.keys(this.buses) as SoundBus[]) {
      this.buses[name].gain.value = settings[name]
    }
  }

  suspendForHidden(hidden: boolean): void {
    this.master.gain.value = hidden ? 0 : getAudioSettings().muted ? 0 : getAudioSettings().master
  }
}
