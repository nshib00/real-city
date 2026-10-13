import type { PlacedBuilding } from '../state/useGameStore'
import type { AssetAnimationManifest, BuildingAnimationKey } from './assetManifestTypes'
import { buildingAssetState, buildingRegistryEntry } from './buildingRegistry'
import type { BuildingAssetState } from './buildingAssetManifests'
import { isCriticallyDamaged } from './buildingDamage'

export type BuildingVisualState = {
  baseState: BuildingAssetState | null
  overlays: BuildingAnimationOverlay[]
}

export type BuildingAnimationOverlay = {
  key: BuildingAnimationKey
  animation: AssetAnimationManifest
}

export function buildingVisualState(building: PlacedBuilding): BuildingVisualState {
  const manifest = buildingRegistryEntry(building.kind)
  const baseState = buildingAssetState(building, manifest)

  if (!manifest?.animations) {
    return { baseState, overlays: [] }
  }

  return {
    baseState,
    overlays: buildingOverlayKeys(building, baseState)
      .map((key) => ({ key, animation: manifest.animations?.[key] }))
      .filter((item): item is BuildingAnimationOverlay => Boolean(item.animation)),
  }
}

export function buildingOverlayKeys(building: PlacedBuilding, baseState = buildingAssetState(building)): BuildingAnimationKey[] {
  const overlays: BuildingAnimationKey[] = []

  if (baseState === 'construction') {
    overlays.push('construction_dust')
  }

  if (baseState === 'active' && building.status === 'active' && building.health > 0) {
    overlays.push('working')
  }

  if (baseState === 'damaged' || isCriticallyDamaged(building)) {
    overlays.push('damaged_smoke')
  }

  if (building.health > 0 && building.maxHealth && building.health / building.maxHealth <= 0.1) {
    overlays.push('damaged_fire')
  }

  if (building.fieldStageReady) {
    overlays.push('ready_to_collect')
  }

  return overlays
}
