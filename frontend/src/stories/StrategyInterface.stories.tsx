import { AlliancePanel } from '../features/alliance/AlliancePanel'
import { EventLog } from '../features/event-log/EventLog'
import { ResourceBar } from '../features/hud/ResourceBar'
import { Inspector } from '../features/inspector/Inspector'
import { NotificationCenter } from '../features/notifications/NotificationCenter'
import { ResourceRegistry } from '../features/resources/ResourceRegistry'
import { ToolBar } from '../features/tools/ToolBar'
import { useGameStore } from '../game/state/useGameStore'

export default {
  title: 'Strategy Interface',
}

export function DesktopHud() {
  useGameStore.setState({
    selectedTile: { x: 4, y: -2 },
    uiPreferences: { compactPanels: false, resourceRegistryOpen: true, alliancePanelOpen: true, buildMenuOpen: false, isChatCollapsed: false, areNotificationsCollapsed: false },
  })

  return (
    <main className="game-shell">
      <ResourceBar />
      <ToolBar />
      <Inspector />
      <EventLog />
      <NotificationCenter />
      <ResourceRegistry />
      <AlliancePanel />
    </main>
  )
}
