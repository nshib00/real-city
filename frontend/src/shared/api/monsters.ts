import { request } from './client'

export type MonsterResponse = {
  id: string
  type: 'roaming_melee' | 'resource_guardian' | 'ruins_guardian'
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

export function listMonsters(input: { x: number; y: number; radius: number }) {
  return request<{ monsters: MonsterResponse[] }>(`/monsters?x=${input.x}&y=${input.y}&radius=${input.radius}`)
}

export function attackMonster(id: string) {
  return request<{ monster: MonsterResponse; rewards: { resource: string; amount: number }[] }>(`/monsters/${id}/attack`, {
    method: 'POST',
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
