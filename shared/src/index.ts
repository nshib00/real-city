export type Coord = {
  x: number
  y: number
}

export type ChunkCoord = {
  x: number
  y: number
}

export type TerrainType = 'grass' | 'forest' | 'water' | 'mountain' | 'road' | 'oil_well' | 'ruins'

export type WorldMap = {
  id: string
  name: string
  seed: number
  chunk_size: number
  spawn_radius: number
}

export type WorldTile = {
  x: number
  y: number
  chunk_x: number
  chunk_y: number
  terrain: TerrainType
  elevation: number
  safe_zone: boolean
  forest_density: number
}

export type WorldChunk = {
  map_id: string
  chunk_x: number
  chunk_y: number
  version: number
  tiles: WorldTile[]
}

export type ObjectKind = 'building' | 'resource_node' | 'monster' | 'terrain'

export type ObjectRef = {
  id: string
  type: ObjectKind
}

export type WorldEventType =
  | 'tile.changed'
  | 'building.placed'
  | 'resource.changed'
  | 'monster.moved'

export type APIErrorKind =
  | 'bad_request'
  | 'validation'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'rate_limited'
  | 'internal'

export type APIError = {
  kind: APIErrorKind
  message: string
  fields?: Record<string, string>
}
