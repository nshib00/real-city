import { request } from './client'
import { normalizeTile } from '../../../../shared/world/coordinates'
import type { InventoryItem, InventoryResponse } from './economy'
import type { BuildingResponse } from './buildings'

export type MonsterResponse = {
  id: string
  type: 'roaming_melee' | 'resource_guardian' | 'ruins_guardian' | 'forest_stalker' | 'spore_beast' | 'ironback_brute' | 'ember_wisp' | 'ancient_colossus'
  state: 'idle' | 'wandering' | 'aggro' | 'attacking' | 'dead'
  tile_x: number
  tile_y: number
  target_id: string
  target_type: string
  health: number
  max_health: number
  damage: number
  aggro_radius: number
  updated_at: string
  creator_id?: string
  expires_at?: string
}

export type ThreatResponse = {
  tile_x: number
  tile_y: number
  level: number
  monster_ids: string[]
}

export type MonsterLootResponse = {
  id: string
  monster_id: string
  tile_x: number
  tile_y: number
  items: InventoryItem[]
  created_at: string
}

export function listMonsterLoot(input: { x: number; y: number; radius: number }) {
  input = { ...input, ...normalizeTile(input) }
  return request<{ loot: MonsterLootResponse[] }>(`/monster-loot?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export function claimMonsterLoot(id: string) {
  return request<{ loot: MonsterLootResponse; inventory: InventoryResponse }>(`/monster-loot/${encodeURIComponent(id)}/claim`, { method: 'POST' })
}

export function listMonsters(input: { x: number; y: number; radius: number }) {
  input = { ...input, ...normalizeTile(input) }
  return request<{ monsters: MonsterResponse[] }>(`/monsters?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export type WeaponAttackResponse = {
  attack: { id: string; weapon: string; due_at: string }
  monster?: MonsterResponse
  loot?: MonsterLootResponse
  building?: BuildingResponse
}

export type PendingWeaponAttack = { id: string; monster_id?: string; building_id?: string; weapon: string; due_at: string }

export function useWeaponOnBuilding(id: string, weapon: string) {
  return request<WeaponAttackResponse>(`/buildings/${encodeURIComponent(id)}/weapons`, { method: 'POST', body: JSON.stringify({ weapon }) })
}

export function createAttackMonster(targetBuildingId: string) {
  return request<{ monster: MonsterResponse }>('/combat/monsters', { method: 'POST', body: JSON.stringify({ target_building_id: targetBuildingId }) })
}

export function listPendingWeaponAttacks() {
  return request<{ attacks: PendingWeaponAttack[] }>('/combat/attacks')
}

export function useWeaponOnMonster(id: string, weapon: string) {
  const key = globalThis.crypto?.randomUUID?.() ?? `weapon-${Date.now()}-${Math.random()}`
  return request<WeaponAttackResponse>(`/monsters/${encodeURIComponent(id)}/weapons`, {
    method: 'POST',
    headers: { 'Idempotency-Key': key },
    body: JSON.stringify({ weapon }),
  })
}

export function listThreats(input: { x: number; y: number; radius: number }) {
  input = { ...input, ...normalizeTile(input) }
  return request<{ threats: ThreatResponse[] }>(`/threats?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export function toMonster(item: MonsterResponse) {
  return {
    id: item.id,
    creatorId: item.creator_id,
    expiresAt: item.expires_at ? Date.parse(item.expires_at) : undefined,
    type: item.type,
    state: item.state,
    tile: { x: item.tile_x, y: item.tile_y },
    targetId: item.target_id,
    targetType: item.target_type,
    health: item.health,
    maxHealth: item.max_health,
    damage: item.damage,
    aggroRadius: item.aggro_radius,
    updatedAt: Date.parse(item.updated_at),
  }
}

export type CombatRules = { attack_range_tiles: number; attack_cooldown_seconds: number; summon_cost_coins: number; summon_cooldown_seconds: number; summon_max_alive: number; summon_lifetime_seconds: number }

export function getCombatRules() {
  return request<{ rules: CombatRules }>('/combat/rules')
}
