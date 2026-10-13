export type AssetAnchor = readonly [number, number]
export type AssetSize = readonly [number, number]
export type AssetFootprint = readonly [number, number]

export type AssetTextureFormat = 'png' | 'webp' | 'avif'

export type AssetRenderMode = 'sprite' | 'atlas' | 'glb-preview'

export type AssetRenderManifest = {
  mode: AssetRenderMode
  size?: AssetSize
  preferredFormat?: AssetTextureFormat
  fallbackFormat?: AssetTextureFormat
}

export type AssetAtlasManifest = {
  image: string
  json: string
  revision?: string
}

export type AssetAnimationType = 'base' | 'overlay' | 'shared_overlay'

export type AssetAnimationManifest = {
  type?: AssetAnimationType
  id?: string
  fps: number
  frames?: number
  loop: boolean
  anchor?: AssetAnchor
  framePrefix?: string
  directions?: readonly AssetDirection[]
}

export type AssetGlbManifest = {
  lod0?: string
  lod1?: string
  lod2?: string
  preview?: string
}

export type AssetDirection = 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw'

export type BuildingAnimationKey =
  | 'construction_dust'
  | 'working'
  | 'damaged_smoke'
  | 'damaged_fire'
  | 'ready_to_collect'
  | 'under_attack'

export type MonsterAnimationKey = 'idle' | 'walk' | 'attack' | 'hit' | 'death' | 'spawn' | 'roar'

export type RuntimeAssetManifest = {
  assetId: string
  anchor?: AssetAnchor
  footprint?: AssetFootprint
  render?: AssetRenderManifest
  atlas?: AssetAtlasManifest
  animations?: Partial<Record<BuildingAnimationKey | MonsterAnimationKey | string, AssetAnimationManifest>>
  glb?: AssetGlbManifest
}
