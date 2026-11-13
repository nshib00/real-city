import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Modal } from '../../shared/ui/Modal'
import { SlidersHorizontal } from '../../shared/ui/icons'
import { getAudioSettings, onAudioSettings, updateAudioSettings, type AudioSettings as Settings } from '../../audio/audioSettings'
import { playUiSound } from '../../audio/playUiSound'

const sliders = [
  ['master', 'Общая громкость', 'ui.confirm'],
  ['ui', 'Интерфейс', 'ui.click'],
  ['world', 'Мир', 'world.forest.cut'],
  ['alerts', 'Предупреждения', 'ui.toast.warning'],
  ['ambience', 'Атмосфера', 'ambience.forest'],
] as const

export function AudioSettings() {
  const [open, setOpen] = useState(false)
  const [settings, setSettings] = useState(getAudioSettings)
  useEffect(() => onAudioSettings(setSettings), [])
  return <div className="audio-settings">
    <button type="button" className="icon-button" aria-label="Настройки звука" title="Настройки звука" aria-expanded={open} data-audio-handled="true" onClick={() => { playUiSound(open ? 'ui.panel.close' : 'ui.panel.open'); setOpen(!open) }}><SlidersHorizontal size={20} /></button>
    {open ? createPortal(<Modal title="Настройки звука" open={open} onClose={() => setOpen(false)} className="audio-settings-modal"><section className="audio-settings-panel">
      {sliders.map(([bus, label, sample]) => <div key={bus}>
        <label htmlFor={`audio-${bus}`}>{label}: {Math.round(settings[bus] * 100)}%</label>
        <input id={`audio-${bus}`} type="range" min="0" max="1" step="0.05" value={settings[bus]}
          onChange={(event) => updateAudioSettings({ [bus]: Number(event.target.value) })} />
        <button type="button" data-audio-handled="true" onClick={() => playUiSound(sample)}>Прослушать</button>
      </div>)}
      <div>
        <label htmlFor="audio-music">Музыка: {Math.round(settings.music * 100)}%</label>
        <input id="audio-music" type="range" min="0" max="1" step="0.05" value={settings.music}
          onChange={(event) => updateAudioSettings({ music: Number(event.target.value) })} />
      </div>
      <label><input type="checkbox" checked={settings.muted} onChange={(event) => updateAudioSettings({ muted: event.target.checked })} />Выключить весь звук</label>
      <label><input type="checkbox" checked={settings.chat} onChange={(event) => updateAudioSettings({ chat: event.target.checked })} />Уведомления чата</label>
      <label><input type="checkbox" checked={settings.reduced} onChange={(event) => updateAudioSettings({ reduced: event.target.checked })} />Меньше одновременных звуков</label>
    </section></Modal>, document.body) : null}
  </div>
}

export type { Settings }
