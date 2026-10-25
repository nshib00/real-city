import { useEffect } from 'react'
import { ErrorBoundary } from './ErrorBoundary'
import { playUiSound, preloadUiSounds } from '../audio/playUiSound'
import { AudioProvider } from '../audio/AudioProvider'
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
import { ToastCenter } from '../features/notifications/ToastCenter'
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
  useEffect(preloadUiSounds, [])
  const showAssetDebugPanel = shouldShowAssetDebugPanel()
  return (
    <ErrorBoundary>
      <AuthGate>
        <AudioProvider />
        <main className="game-shell" onClickCapture={(event) => {
          const target = event.target
          if (!(target instanceof Element)) return
          const button = target.closest('button')
          if (button && !button.disabled && button.dataset.audioHandled !== 'true') playUiSound('ui.click')
        }}>
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
          <ToastCenter />
          <ResourceRegistry />
          <AlliancePanel />
          {showAssetDebugPanel ? <AssetDebugPanel /> : null}
        </main>
      </AuthGate>
    </ErrorBoundary>
  )
}
