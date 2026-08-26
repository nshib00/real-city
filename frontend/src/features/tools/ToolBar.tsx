import { Castle, Hammer, MousePointer2, Route, Swords } from 'lucide-react'

import { useGameStore, type ToolMode } from '../../game/state/useGameStore'
import { IconButton } from '../../shared/ui'

const tools = [
  { id: 'select', label: 'Выбор', icon: MousePointer2 },
  { id: 'build', label: 'Строить', icon: Castle },
  { id: 'road', label: 'Дорога', icon: Route },
  { id: 'repair', label: 'Ремонт', icon: Hammer },
  { id: 'raid', label: 'Рейд', icon: Swords },
] satisfies readonly { id: ToolMode; label: string; icon: typeof MousePointer2 }[]

export function ToolBar() {
  const activeTool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)

  return (
    <nav className="tool-bar" aria-label="Инструменты">
      {tools.map((tool) => {
        const onClick = tool.id === 'build' ? () => setBuildMenuOpen(true) : () => setTool(tool.id)
        return <IconButton key={tool.id} label={tool.label} icon={tool.icon} active={activeTool === tool.id} onClick={onClick} />
      })}
    </nav>
  )
}
