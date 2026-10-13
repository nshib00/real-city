import type { ObjectAtlasSource } from '../renderer/objectLayer/objectTextureCache'
import type { PlacedBuilding } from '../state/useGameStore'
import { dugoutModelLevel, dugoutModelState } from './dugout'
import { flaxFieldModelLevel, flaxFieldModelState } from './flaxField'
import { glassWorkshopModelLevel, glassWorkshopModelState } from './glassWorkshop'
import { lumberYardModelLevel, lumberYardModelState } from './lumberYard'
import { mineModelLevel, mineModelState } from './mine'
import { oilseedFieldModelLevel, oilseedFieldModelState } from './oilseedField'
import { ropeYardModelLevel, ropeYardModelState } from './ropeYard'
import { sandQuarryModelLevel, sandQuarryModelState } from './sandQuarry'
import { seedGardenModelLevel, seedGardenModelState } from './seedGarden'
import { townHallModelLevel, townHallModelState } from './townHall'
import { windleafBedModelLevel, windleafBedModelState } from './windleafBed'
import { woodHouseModelLevel, woodHouseModelState } from './woodHouse'
import { buildingAssetManifests, type BuildingAssetManifest, type BuildingAssetState } from './buildingAssetManifests'
import { isCriticallyDamaged } from './buildingDamage'

type BuildingAssetExtension = 'png' | 'glb'
type BuildingAssetLookupOptions = {
  extension: BuildingAssetExtension
  shape?: string
}

type ManifestPolicy = {
  level: (level: number) => number
  state: (building: PlacedBuilding) => BuildingAssetState
}

const registry = new Map(buildingAssetManifests.map((manifest) => [manifest.kind, manifest]))

const srcModelUrlLoaders = import.meta.glob('../../assets/buildings/**/*.glb', {
  query: '?url',
  import: 'default',
}) as Record<string, () => Promise<string>>

const manifestPolicies: Partial<Record<PlacedBuilding['kind'], ManifestPolicy>> = {
  town_hall: { level: townHallModelLevel, state: (building) => townHallModelState(building) },
  dugout: { level: dugoutModelLevel, state: (building) => dugoutModelState(building) },
  wood_house: { level: woodHouseModelLevel, state: (building) => woodHouseModelState(building) },
  field_bed: { level: windleafBedModelLevel, state: (building) => windleafBedModelState(building) },
  seed_garden: { level: seedGardenModelLevel, state: (building) => seedGardenModelState(building) },
  flax_field: { level: flaxFieldModelLevel, state: (building) => flaxFieldModelState(building) },
  herb_bed: { level: herbBedModelLevel, state: (building) => seedGardenModelState(building) },
  mushroom_grove: { level: seedGardenModelLevel, state: (building) => seedGardenModelState(building) },
  reed_bed: { level: seedGardenModelLevel, state: (building) => seedGardenModelState(building) },
  oilseed_field: { level: oilseedFieldModelLevel, state: (building) => oilseedFieldModelState(building) },
  lumber_yard: { level: lumberYardModelLevel, state: (building) => lumberYardModelState(building) },
  sand_quarry: { level: sandQuarryModelLevel, state: (building) => sandQuarryModelState(building) },
  mine: { level: mineModelLevel, state: (building) => mineModelState(building) },
  glass_workshop: { level: glassWorkshopModelLevel, state: (building) => glassWorkshopModelState(building) },
  rope_yard: { level: ropeYardModelLevel, state: (building) => ropeYardModelState(building) },
}

export function buildingRegistryEntry(kind: PlacedBuilding['kind']) {
  return registry.get(kind) ?? null
}

export function registeredBuildingAssetFamilies() {
  return [...buildingAssetManifests]
}

export function buildingAssetLevel(building: PlacedBuilding, manifest = buildingRegistryEntry(building.kind)) {
  if (!manifest) {
    return null
  }
  const policyLevel = manifestPolicies[building.kind]?.level(building.level) ?? clampLevel(building.level, manifest.levels)
  return clampLevel(policyLevel, manifest.levels)
}

export function buildingAssetState(building: PlacedBuilding, manifest = buildingRegistryEntry(building.kind)): BuildingAssetState | null {
  if (!manifest) {
    return null
  }
  const policyState = manifestPolicies[building.kind]?.state(building) ?? defaultBuildingAssetState(building)
  return stateOrFallback(policyState, manifest)
}

export function resolveBuildingSpriteAsset(building: PlacedBuilding, options: Omit<BuildingAssetLookupOptions, 'extension'> = {}) {
  return resolveBuildingAsset(building, { ...options, extension: 'png' })
}

export function resolveBuildingModelAsset(building: PlacedBuilding, options: Omit<BuildingAssetLookupOptions, 'extension'> = {}) {
  return resolveBuildingAsset(building, { ...options, extension: 'glb' })
}

export function canResolveBuildingModelAsset(building: PlacedBuilding, options: Omit<BuildingAssetLookupOptions, 'extension'> = {}) {
  const locator = resolveBuildingAssetLocator(building, { ...options, extension: 'glb' })
  if (!locator) {
    return false
  }
  return locator.source === 'public' || Boolean(srcModelUrlLoaders[locator.srcModelKey])
}

export async function resolveBuildingModelAssetUrl(building: PlacedBuilding, options: Omit<BuildingAssetLookupOptions, 'extension'> = {}) {
  return resolveBuildingAssetUrl(building, { ...options, extension: 'glb' })
}

export function resolveBuildingAtlasSource(building: PlacedBuilding, options: Omit<BuildingAssetLookupOptions, 'extension'> = {}): ObjectAtlasSource | null {
  const manifest = buildingRegistryEntry(building.kind)
  if (!manifest) {
    return null
  }

  const level = buildingAssetLevel(building, manifest)
  const state = buildingAssetState(building, manifest)
  if (!level || !state) {
    return null
  }

  const frameName = buildingAssetFileName(manifest, level, state, { ...options, extension: 'png' })
  return {
    assetId: manifest.assetId,
    basePath: `/assets/buildings/${manifest.category}/${manifest.assetId}`,
    atlas: manifest.atlas,
    revision: manifest.revision,
    fallbackUrl: resolveBuildingSpriteAsset(building, options),
    requiredFrames: [frameName, ...buildingAnimationFrameNames(manifest)],
  }
}

export function resolveBuildingAsset(building: PlacedBuilding, options: BuildingAssetLookupOptions) {
  const locator = resolveBuildingAssetLocator(building, options)
  if (!locator) {
    return null
  }

  if (locator.source === 'src-models') {
    return null
  }

  return locator.revision ? withAssetRevision(locator.asset, locator.revision) : locator.asset
}

export async function resolveBuildingAssetUrl(building: PlacedBuilding, options: BuildingAssetLookupOptions) {
  const locator = resolveBuildingAssetLocator(building, options)
  if (!locator) {
    return null
  }

  if (locator.source === 'src-models') {
    const asset = await srcModelUrlLoaders[locator.srcModelKey]?.()
    return asset ? withOptionalAssetRevision(asset, locator.revision) : null
  }

  return withOptionalAssetRevision(locator.asset, locator.revision)
}

function resolveBuildingAssetLocator(building: PlacedBuilding, options: BuildingAssetLookupOptions) {
  const manifest = buildingRegistryEntry(building.kind)
  if (!manifest) {
    return null
  }
  const level = buildingAssetLevel(building, manifest)
  const state = buildingAssetState(building, manifest)
  if (!level || !state) {
    return null
  }

  const fileName = buildingAssetFileName(manifest, level, state, options)
  const source = options.extension === 'glb' ? manifest.modelSource : manifest.spriteSource
  const srcModelKey = `../../assets/buildings/${manifest.category}/${manifest.assetId}/${fileName}`
  const asset = `/assets/buildings/${manifest.category}/${manifest.assetId}/${fileName}`

  return { asset, fileName, revision: manifest.revision, source, srcModelKey }
}

export function buildingAssetFileName(manifest: BuildingAssetManifest, level: number, state: BuildingAssetState, options: BuildingAssetLookupOptions) {
  const extension = options.extension
  if (manifest.shapeDefault) {
    const shape = options.shape ?? manifest.shapeDefault
    return `${manifest.assetId}_${shape}_${state}.${extension}`
  }
  return `${manifest.assetId}_l${String(level).padStart(2, '0')}_${state}.${extension}`
}

export function withAssetRevision(asset: string, revision: string) {
  return `${asset}?v=${revision}`
}

function withOptionalAssetRevision(asset: string, revision: string | undefined) {
  return revision ? withAssetRevision(asset, revision) : asset
}

function clampLevel(level: number, levels: readonly number[]) {
  const value = Math.round(level || 1)
  const sorted = [...levels].sort((left, right) => left - right)
  return Math.max(sorted[0] ?? 1, Math.min(sorted[sorted.length - 1] ?? 1, value))
}

function herbBedModelLevel(level: number) {
  return Math.max(1, Math.min(9, Math.round(level || 1)))
}

function defaultBuildingAssetState(building: PlacedBuilding): BuildingAssetState {
  if (building.state === 'ruined' || building.health <= 0) {
    return 'ruined'
  }
  if (building.status === 'construction' || building.state === 'building' || building.state === 'planned') {
    return 'construction'
  }
  if (isCriticallyDamaged(building)) {
    return 'damaged'
  }
  return 'active'
}

function stateOrFallback(state: BuildingAssetState, manifest: BuildingAssetManifest): BuildingAssetState {
  if (manifest.states.includes(state)) {
    return state
  }
  if (state === 'ruined' && manifest.states.includes('damaged')) {
    return 'damaged'
  }
  if ((state.startsWith('stage') || state.startsWith('super_stage')) && manifest.states.includes('active')) {
    return 'active'
  }
  return manifest.states.includes('active') ? 'active' : manifest.states[0]
}

function buildingAnimationFrameNames(manifest: BuildingAssetManifest) {
  if (!manifest.animations) {
    return []
  }

  return Object.values(manifest.animations).flatMap((animation) => {
    if (!animation?.framePrefix || !animation.frames) {
      return []
    }
    return Array.from({ length: animation.frames }, (_, index) => `${animation.framePrefix}${String(index).padStart(4, '0')}.png`)
  })
}
