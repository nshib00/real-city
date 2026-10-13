import { ErrorBoundary } from './ErrorBoundary'
import { AlliancePanel } from '../features/alliance/AlliancePanel'
import { AssetDebugPanel, shouldShowAssetDebugPanel } from '../features/assets/AssetDebugPanel'
import { AuthGate } from '../features/auth/AuthGate'
import { BuildingSync } from '../features/buildings/BuildingSync'
import { BuildMenu } from '../features/buildings/BuildMenu'
import { ConstructionTicker } from '../features/buildings/ConstructionTicker'
import { EventLog } from '../features/event-log/EventLog'
import { ResourceBar } from '../features/hud/ResourceBar'
import { Inspector } from '../features/inspector/Inspector'
import { NotificationCenter } from '../features/notifications/NotificationCenter'
import { MonsterSync } from '../features/monster/MonsterSync'
import { ProfilePanel } from '../features/player/ProfilePanel'
import { ProductionPanel } from '../features/production/ProductionPanel'
import { ResourceRegistry } from '../features/resources/ResourceRegistry'
import { ResourceNodeSync } from '../features/resources/ResourceNodeSync'
import { ToolBar } from '../features/tools/ToolBar'
import { MapWidget } from '../features/world-map/MapWidget'
import { WorldRealtime } from '../features/world/WorldRealtime'
import { IsoMap } from '../game/IsoMap'

export function App() {
  const showAssetDebugPanel = shouldShowAssetDebugPanel()
  return (
    <ErrorBoundary>
      <AuthGate>
        <main className="game-shell">
          <ResourceBar />
          <ProfilePanel />
          <ToolBar />
          <MapWidget />
          <BuildMenu />
          <BuildingSync />
          <ResourceNodeSync />
          <MonsterSync />
          <WorldRealtime />
          <ConstructionTicker />
          <IsoMap />
          <Inspector />
          <ProductionPanel />
          <EventLog />
          <NotificationCenter />
          <ResourceRegistry />
          <AlliancePanel />
          {showAssetDebugPanel ? <AssetDebugPanel /> : null}
        </main>
      </AuthGate>
    </ErrorBoundary>
  )
}
