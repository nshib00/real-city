import { request } from './client'
import type { BuildingKind, BuildingState, PlacedBuilding } from '../../game/state/useGameStore'

export type BuildingResponse = {
  id: string
  owner_id: string
  type: BuildingKind
  name: string
  level: number
  state: BuildingState
  health: number
  max_health?: number
  tile_x: number
  tile_y: number
  started_at: string
  completes_at: string | null
  field_stage?: number
  growth_stage?: number
  crop_stage?: number
  super_stage?: number
  field_stage_started_at?: string | null
  field_stage_ready_at?: string | null
  field_stage_ready?: boolean
  is_super_crop?: boolean
  super_crop?: boolean
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

export function patchBuilding(id: string, action: 'complete' | 'rush_complete' | 'cancel' | 'repair' | 'upgrade') {
  return request<{ building?: BuildingResponse; status?: string; inventory?: unknown; rush?: { crystal_cost: number } }>(`/buildings/${id}`, {
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
    state: response.state,
    health: response.health,
    maxHealth: response.max_health,
    owner: response.owner_id,
    startedAt: Date.parse(response.started_at),
    completesAt: response.completes_at ? Date.parse(response.completes_at) : null,
    fieldStage: response.field_stage,
    growthStage: response.growth_stage,
    cropStage: response.crop_stage,
    superStage: response.super_stage,
    fieldStageStartedAt: response.field_stage_started_at ? Date.parse(response.field_stage_started_at) : null,
    fieldStageReadyAt: response.field_stage_ready_at ? Date.parse(response.field_stage_ready_at) : null,
    fieldStageReady: response.field_stage_ready,
    isSuperCrop: response.is_super_crop,
    superCrop: response.super_crop,
  }
}
