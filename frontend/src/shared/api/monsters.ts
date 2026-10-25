import { request } from './client'
import type { InventoryItem, InventoryResponse } from './economy'

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
  return request<{ loot: MonsterLootResponse[] }>(`/monster-loot?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export function claimMonsterLoot(id: string) {
  return request<{ loot: MonsterLootResponse; inventory: InventoryResponse }>(`/monster-loot/${encodeURIComponent(id)}/claim`, { method: 'POST' })
}

export function listMonsters(input: { x: number; y: number; radius: number }) {
  return request<{ monsters: MonsterResponse[] }>(`/monsters?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export type WeaponAttackResponse = {
  attack: { id: string; weapon: string; due_at: string }
  monster?: MonsterResponse
  loot?: MonsterLootResponse
}

export type PendingWeaponAttack = { id: string; monster_id: string; weapon: string; due_at: string }

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
  return request<{ threats: ThreatResponse[] }>(`/threats?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export function toMonster(item: MonsterResponse) {
  return {
    id: item.id,
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
