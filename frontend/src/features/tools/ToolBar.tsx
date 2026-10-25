import { useState } from 'react'
import { Castle, Hammer, MousePointer2, Route, Swords, Volume2, VolumeX, Waves } from 'lucide-react'

import { isUiSoundMuted, playUiSound, setUiSoundMuted } from '../../audio/playUiSound'
import { isAmbienceEnabled, setAmbienceEnabled } from '../../audio/ambience'
import { useGameStore, type ToolMode } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { AudioSettings } from '../settings/AudioSettings'

const tools = [
  { id: 'select', label: 'Выбор', icon: MousePointer2 },
  { id: 'build', label: 'Строить', icon: Castle },
  { id: 'road', label: 'Дорога', icon: Route },
  { id: 'repair', label: 'Ремонт', icon: Hammer },
  { id: 'raid', label: 'Рейд', icon: Swords },
] satisfies readonly { id: ToolMode; label: string; icon: typeof MousePointer2 }[]

export function ToolBar() {
  const [muted, setMuted] = useState(isUiSoundMuted)
  const [ambienceEnabled, setAmbienceEnabledState] = useState(isAmbienceEnabled)
  const activeTool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)

  return (
    <nav className="tool-bar" aria-label="Инструменты">
      {tools.map((tool) => {
        const onClick = tool.id === 'build' ? () => setBuildMenuOpen(true) : () => setTool(tool.id)
        return <IconButton key={tool.id} label={tool.label} icon={tool.icon} active={activeTool === tool.id} sound={tool.id === 'build' ? 'ui.panel.open' : 'ui.click'} onClick={onClick} />
      })}
      <IconButton
        label={ambienceEnabled ? 'Выключить атмосферу' : 'Включить атмосферу'}
        icon={Waves}
        active={ambienceEnabled}
        onClick={() => { const next = !ambienceEnabled; setAmbienceEnabled(next); setAmbienceEnabledState(next) }}
      />
      <IconButton
        label={muted ? 'Включить звук' : 'Выключить звук'}
        icon={muted ? VolumeX : Volume2}
        active={!muted}
        sound="ui.toggle.off"
        onClick={() => {
          const next = !muted
          setUiSoundMuted(next)
          setMuted(next)
          if (!next) playUiSound('ui.toggle.on')
        }}
      />
      <AudioSettings />
    </nav>
  )
}
