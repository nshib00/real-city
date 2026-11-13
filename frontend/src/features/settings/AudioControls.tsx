import { useState } from 'react'
import { isUiSoundMuted, setUiSoundMuted, playUiSound } from '../../audio/playUiSound'
import { isAmbienceEnabled, setAmbienceEnabled } from '../../audio/ambience'
import { Volume2, VolumeX, Waves, Gauge } from '../../shared/ui/icons'
import { IconButton } from '../../shared/ui'
import { AudioSettings } from './AudioSettings'
import { useGameStore } from '../../game/state/useGameStore'

export function AudioControls() {
  const [muted, setMuted] = useState(isUiSoundMuted)
  const [ambience, setAmbience] = useState(isAmbienceEnabled)
  const mapPowerSave = useGameStore((state) => state.uiPreferences.mapPowerSave)
  const setMapPowerSave = useGameStore((state) => state.setMapPowerSave)
  return <aside className="audio-controls" aria-label="Управление звуком">
    <IconButton label={mapPowerSave ? 'Выключить оптимизированный интерфейс (до 30 FPS)' : 'Включить оптимизированный интерфейс (до 30 FPS)'} icon={Gauge} active={mapPowerSave} onClick={() => setMapPowerSave(!mapPowerSave)} />
    <IconButton label={ambience ? 'Выключить атмосферу' : 'Включить атмосферу'} icon={Waves} active={ambience} onClick={() => { const next = !ambience; setAmbience(next); setAmbienceEnabled(next) }} />
    <IconButton label={muted ? 'Включить звук' : 'Выключить звук'} icon={muted ? VolumeX : Volume2} active={!muted} onClick={() => { const next = !muted; setMuted(next); setUiSoundMuted(next); if (!next) playUiSound('ui.toggle.on') }} />
    <AudioSettings />
  </aside>
}
