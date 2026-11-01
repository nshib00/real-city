import { request } from './client'
import { normalizeTile } from '../../../../shared/world/coordinates'
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
  cannon_enabled?: boolean
  cannon_next_attack_at?: string | null
  cannon_target_id?: string
  cannon_range?: number
  cannon_damage?: number
  cannon_ammo?: string
  cannon_cooldown_seconds?: number
  cannon_damage_type?: string
  trap_charges?: number
  trap_max_charges?: number
  trap_damage?: number
  defense_slots?: number
  defense_patrol_radius?: number
  defense_staff_role?: string
  demolition_refund_coins?: number
  tile_x: number
  tile_y: number
  rotation?: number
  footprint_w?: number
  footprint_h?: number
  started_at: string
  created_at?: string
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
  health: number
  cost: { resource: string; amount: number }[]
  first_level: boolean
  upgrade_levels: {
    level: number
    build_seconds: number
    population: number
    health: number
    cost: { resource: string; amount: number }[]
    next_type?: BuildingKind
  }[]
  requires_town_hall: boolean
  counts_toward_limit: boolean
  upgrade_to: BuildingKind[]
}

export function listBuildingCatalog() {
  return request<{ buildings: BuildingCatalogResponse[] }>('/buildings/catalog')
}

export function listFullBuildingCatalog() {
  return request<{ buildings: BuildingCatalogResponse[] }>('/buildings/catalog?scope=all')
}

export function listBuildings() {
  return request<{ buildings: BuildingResponse[] }>('/buildings')
}

export function listVisibleBuildings(center: { x: number; y: number }, radius: number) {
  center = normalizeTile(center)
  return request<{ buildings: BuildingResponse[] }>(`/buildings?scope=visible&x=${center.x}&y=${center.y}&radius=${radius}`)
}

export function placeBuilding(input: { type: BuildingKind; tile_x: number; tile_y: number }) {
  const tile = normalizeTile({ x: input.tile_x, y: input.tile_y })
  return request<{ building: BuildingResponse }>('/buildings', {
    method: 'POST',
    body: JSON.stringify({ ...input, tile_x: tile.x, tile_y: tile.y }),
  })
}

export function patchBuilding(id: string, action: 'complete' | 'rush_complete' | 'cancel' | 'repair' | 'upgrade' | 'enable_cannon' | 'disable_cannon' | 'reload_trap', targetType?: BuildingKind) {
  return request<{ building?: BuildingResponse; status?: string; inventory?: unknown; rush?: { crystal_cost: number } }>(`/buildings/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action, ...(targetType ? { target_type: targetType } : {}) }),
  })
}

export function relocateBuilding(id: string, tile: { x: number; y: number }, rotation: number) {
  tile = normalizeTile(tile)
  return request<{ building: BuildingResponse }>(`/buildings/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action: 'relocate', tile_x: tile.x, tile_y: tile.y, rotation }),
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
    rotation: response.rotation ?? 0,
    footprintW: response.footprint_w,
    footprintH: response.footprint_h,
    status: response.state === 'building' || response.state === 'planned' ? 'construction' : 'active',
    state: response.state,
    health: response.health,
    maxHealth: response.max_health,
    cannonEnabled: response.cannon_enabled,
    cannonNextAttackAt: response.cannon_next_attack_at ? Date.parse(response.cannon_next_attack_at) : null,
    cannonTargetId: response.cannon_target_id,
    cannonRange: response.cannon_range,
    cannonDamage: response.cannon_damage,
    cannonAmmo: response.cannon_ammo,
    cannonCooldownSeconds: response.cannon_cooldown_seconds,
    cannonDamageType: response.cannon_damage_type,
    trapCharges: response.trap_charges,
    trapMaxCharges: response.trap_max_charges,
    trapDamage: response.trap_damage,
    defenseSlots: response.defense_slots,
    defensePatrolRadius: response.defense_patrol_radius,
    defenseStaffRole: response.defense_staff_role,
    demolitionRefundCoins: response.demolition_refund_coins,
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

export type RepairQuote = { cost: { resource: string; amount: number }[]; workers: number; duration_seconds: number; job?: { id: string; due_at: string; status: string } }
export function getRepairStatus(id: string) { return request<{ repair: RepairQuote }>(`/buildings/${encodeURIComponent(id)}/repair`) }
