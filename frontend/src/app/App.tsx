import { lazy, Suspense, useEffect } from 'react'
import { useApplyInterfaceTheme } from './theme'
import { InterfaceNavigation } from './InterfaceNavigation'
import { ActionFeedback } from '../features/notifications/ActionFeedback'
import { MapAssetStatus } from '../features/notifications/MapAssetStatus'
import { ErrorBoundary } from './ErrorBoundary'
import { playUiSound, preloadUiSounds } from '../audio/playUiSound'
import { AudioProvider } from '../audio/AudioProvider'
import { AuthGate } from '../features/auth/AuthGate'
import { useAuthStore } from '../features/auth/useAuthStore'
import { BuildingSync } from '../features/buildings/BuildingSync'
import { ConstructionTicker } from '../features/buildings/ConstructionTicker'
import { EventLog } from '../features/event-log/EventLog'
import { ResourceBar } from '../features/hud/ResourceBar'
import { Inspector } from '../features/inspector/Inspector'
import { NotificationCenter } from '../features/notifications/NotificationCenter'
import { ToastCenter } from '../features/notifications/ToastCenter'
import { MonsterSync } from '../features/monster/MonsterSync'
import { ProfilePanel } from '../features/player/ProfilePanel'
import { ProductionPanel } from '../features/production/ProductionPanel'
import { ResourceNodeSync } from '../features/resources/ResourceNodeSync'
import { ToolBar } from '../features/tools/ToolBar'
import { AudioControls } from '../features/settings/AudioControls'
import { WorldRealtime } from '../features/world/WorldRealtime'
import { IsoMap } from '../game/IsoMap'
import { FirstCityHelp } from '../features/buildings/FirstCityHelp'
import { useGameStore } from '../game/state/useGameStore'
import { clientTelemetry } from '../shared/telemetry/clientTelemetry'

const BuildMenu = lazy(() => import('../features/buildings/BuildMenu').then((module) => ({ default: module.BuildMenu })))
const ResourceRegistry = lazy(() => import('../features/resources/ResourceRegistry').then((module) => ({ default: module.ResourceRegistry })))
const AlliancePanel = lazy(() => import('../features/alliance/AlliancePanel').then((module) => ({ default: module.AlliancePanel })))
const AssetDebugPanel = lazy(() => import('../features/assets/AssetDebugPanel').then((module) => ({ default: module.AssetDebugPanel })))

export function App() {
  useApplyInterfaceTheme()
  const playerId = useAuthStore((state) => state.player?.id)
  const buildMenuOpen = useGameStore((state) => state.uiPreferences.buildMenuOpen)
  const resourceRegistryOpen = useGameStore((state) => state.uiPreferences.resourceRegistryOpen)
  const alliancePanelOpen = useGameStore((state) => state.uiPreferences.alliancePanelOpen)
  useEffect(() => { if (buildMenuOpen) clientTelemetry.record('ui_build_panel_open') }, [buildMenuOpen])
  useEffect(() => { if (resourceRegistryOpen) clientTelemetry.record('ui_resource_panel_open') }, [resourceRegistryOpen])
  useEffect(() => { if (alliancePanelOpen) clientTelemetry.record('ui_alliance_panel_open') }, [alliancePanelOpen])
  useEffect(preloadUiSounds, [])
  const showAssetDebugPanel = import.meta.env.DEV && new URLSearchParams(window.location.search).has('assets')
  return (
    <ErrorBoundary>
      <AuthGate>
        <AudioProvider />
        <main key={playerId ?? 'anonymous'} className="game-shell" onClickCapture={(event) => {
          const target = event.target
          if (!(target instanceof Element)) return
          const button = target.closest('button')
          if (button && !button.disabled && button.dataset.audioHandled !== 'true') playUiSound('ui.click')
        }}>
          <InterfaceNavigation />
          <ActionFeedback />
          <MapAssetStatus />
          <ResourceBar />
          <ProfilePanel />
          <ToolBar />
          <AudioControls />
          {buildMenuOpen ? <Suspense fallback={null}><BuildMenu /></Suspense> : null}
          <BuildingSync />
          <ResourceNodeSync />
          <MonsterSync />
          <WorldRealtime />
          <ConstructionTicker />
          <IsoMap />
          <FirstCityHelp key={playerId} />
          <Inspector />
          <ProductionPanel />
          <EventLog />
          <NotificationCenter />
          <ToastCenter />
          {resourceRegistryOpen ? <Suspense fallback={null}><ResourceRegistry /></Suspense> : null}
          {alliancePanelOpen ? <Suspense fallback={null}><AlliancePanel /></Suspense> : null}
          {showAssetDebugPanel ? <Suspense fallback={null}><AssetDebugPanel /></Suspense> : null}
        </main>
      </AuthGate>
    </ErrorBoundary>
  )
}
