import { useEffect } from 'react'
import { Castle, Handshake, MousePointer2 } from '../../shared/ui/icons'

import { useGameStore, type ToolMode } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'
import { AdminPanel } from '../admin/AdminPanel'
import { buildCatalog } from '../buildings/catalog'

const tools = [
  { id: 'select', label: 'Выбор', icon: MousePointer2 },
  { id: 'build', label: 'Строить', icon: Castle },
] satisfies readonly { id: ToolMode; label: string; icon: typeof MousePointer2 }[]

export function ToolBar() {
  const activeTool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)
  const previewKind = useGameStore((state) => state.placementPreviewKind)
  const preview = buildCatalog.find((item) => item.kind === previewKind)
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target instanceof Element ? event.target : null
      if (event.defaultPrevented || event.ctrlKey || event.altKey || event.metaKey || target?.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]')) return
      if (event.key === 'Escape') { setTool('select'); return }
      const index = Number(event.key) - 1
      const tool = tools[index]
      if (!tool) return
      event.preventDefault()
      if (tool.id === 'build') setBuildMenuOpen(true)
      else setTool(tool.id)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setTool, setBuildMenuOpen])

  return (
    <nav id="game-tools" tabIndex={-1} className="tool-bar" aria-label="Инструменты">
      {tools.map((tool, index) => {
        const onClick = tool.id === 'build' ? () => setBuildMenuOpen(true) : () => setTool(tool.id)
        const active = activeTool === tool.id
        return <IconButton key={tool.id} label={tool.label} shortcut={String(index + 1)} icon={tool.icon} active={active} sound={tool.id === 'build' ? 'ui.panel.open' : 'ui.click'} onClick={onClick} />
      })}
      <IconButton label="Меню союза" icon={Handshake} sound="ui.panel.open" onClick={() => setAlliancePanelOpen(true)} />
      <MapWidget />
      <div className="tool-context" role="status">
        <strong>{preview?.name ?? tools.find((item) => item.id === activeTool)?.label}</strong>
        {preview ? <span>{preview.cost.map((cost) => `${cost.label}: ${cost.amount}`).join(', ') || 'Бесплатно'}</span> : null}
        {activeTool !== 'select' || preview ? <button type="button" onClick={() => setTool('select')}>Отмена (Esc)</button> : null}
      </div>
      <AdminPanel />
    </nav>
  )
}

import { MapWidget } from '../world-map/MapWidget'

