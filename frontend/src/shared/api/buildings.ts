import { request } from './client'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'

export type BuildingResponse = {
  id: string
  owner_id: string
  type: BuildingKind
  name: string
  level: number
  state: 'planned' | 'building' | 'active' | 'damaged' | 'ruined'
  health: number
  tile_x: number
  tile_y: number
  started_at: string
  completes_at: string | null
}

export type BuildingCatalogResponse = {
  type: BuildingKind
  category: 'housing' | 'fields' | 'industry' | 'defense' | 'roads' | 'storage' | 'social' | 'trade' | 'center'
  name: string
  level: number
  footprint_w: number
  footprint_h: number
  build_seconds: number
  population: number
  cost: { resource: string; amount: number }[]
  requires_town_hall: boolean
  counts_toward_limit: boolean
  upgrade_to: BuildingKind[]
}

export function listBuildingCatalog() {
  return request<{ buildings: BuildingCatalogResponse[] }>('/buildings/catalog')
}

export function listBuildings() {
  return request<{ buildings: BuildingResponse[] }>('/buildings')
}

export function placeBuilding(input: { type: BuildingKind; tile_x: number; tile_y: number }) {
  return request<{ building: BuildingResponse }>('/buildings', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function patchBuilding(id: string, action: 'complete' | 'cancel' | 'repair' | 'upgrade') {
  return request<{ building?: BuildingResponse; status?: string }>(`/buildings/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action }),
  })
}

export function deleteBuilding(id: string) {
  return request<{ status: string }>(`/buildings/${id}`, { method: 'DELETE' })
}

export function toPlacedBuilding(response: BuildingResponse): PlacedBuilding {
  return {
    id: response.id,
    kind: response.type,
    name: response.name,
    level: response.level,
    tile: { x: response.tile_x, y: response.tile_y },
    status: response.state === 'building' || response.state === 'planned' ? 'construction' : 'active',
    health: response.health,
    owner: response.owner_id,
    startedAt: Date.parse(response.started_at),
    completesAt: response.completes_at ? Date.parse(response.completes_at) : null,
  }
}
