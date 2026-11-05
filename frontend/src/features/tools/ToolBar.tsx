import { useEffect, useState } from 'react'
import { Castle, Repair, MousePointer2, Route, Settings, Swords, Volume2, VolumeX, Waves } from '../../shared/ui/icons'

import { isUiSoundMuted, playUiSound, setUiSoundMuted } from '../../audio/playUiSound'
import { isAmbienceEnabled, setAmbienceEnabled } from '../../audio/ambience'
import { useGameStore, type ToolMode } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { AudioSettings } from '../settings/AudioSettings'
import { AdminPanel } from '../admin/AdminPanel'
import { buildCatalog } from '../buildings/catalog'

const tools = [
  { id: 'select', label: 'Выбор', icon: MousePointer2 },
  { id: 'build', label: 'Строить', icon: Castle },
  { id: 'road', label: 'Дорога', icon: Route },
  { id: 'repair', label: 'Ремонт', icon: Repair },
  { id: 'attack', label: 'Атака', icon: Swords },
] satisfies readonly { id: ToolMode; label: string; icon: typeof MousePointer2 }[]

export function ToolBar() {
  const [muted, setMuted] = useState(isUiSoundMuted)
  const [ambienceEnabled, setAmbienceEnabledState] = useState(isAmbienceEnabled)
  const activeTool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const mapPowerSave = useGameStore((state) => state.uiPreferences.mapPowerSave)
  const setMapPowerSave = useGameStore((state) => state.setMapPowerSave)
  const previewKind = useGameStore((state) => state.placementPreviewKind)
  const preview = buildCatalog.find((item) => item.kind === previewKind)
  const openRoads = () => {
    setBuildMenuOpen(true)
    useGameStore.getState().setPlacementPreviewKind('road')
  }
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target instanceof Element ? event.target : null
      if (event.defaultPrevented || event.ctrlKey || event.altKey || event.metaKey || target?.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]')) return
      if (event.key === 'Escape') { setTool('select'); return }
      const index = Number(event.key) - 1
      const tool = tools[index]
      if (!tool) return
      event.preventDefault()
      if (tool.id === 'road') { setBuildMenuOpen(true); useGameStore.getState().setPlacementPreviewKind('road') }
      else if (tool.id === 'build') setBuildMenuOpen(true)
      else setTool(tool.id)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setTool, setBuildMenuOpen])

  return (
    <nav id="game-tools" tabIndex={-1} className="tool-bar" aria-label="Инструменты">
      {tools.map((tool, index) => {
        const onClick = tool.id === 'road' ? openRoads : tool.id === 'build' ? () => setBuildMenuOpen(true) : () => setTool(tool.id)
        const active = preview?.category === 'roads' ? tool.id === 'road' : activeTool === tool.id
        return <IconButton key={tool.id} label={tool.label} shortcut={String(index + 1)} icon={tool.icon} active={active} sound={tool.id === 'build' ? 'ui.panel.open' : 'ui.click'} onClick={onClick} />
      })}
      <div className="tool-context" role="status">
        <strong>{preview?.name ?? tools.find((item) => item.id === activeTool)?.label}</strong>
        {preview || activeTool === 'repair' || activeTool === 'attack' ? <span>{preview ? preview.cost.map((cost) => `${cost.label}: ${cost.amount}`).join(', ') || 'Бесплатно' : activeTool === 'repair' ? 'Выберите постройку, чтобы открыть меню ремонта' : 'Расход оружия — в карточке цели'}</span> : null}
        {activeTool !== 'select' || preview ? <button type="button" onClick={() => setTool('select')}>Отмена (Esc)</button> : null}
      </div>
      <IconButton label="Экономный режим карты" icon={Settings} active={mapPowerSave} onClick={() => setMapPowerSave(!mapPowerSave)} />
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
      <AdminPanel />
    </nav>
  )
}
