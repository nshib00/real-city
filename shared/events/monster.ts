export type MonsterEventType = 'monster.spawned' | 'monster.moved' | 'monster.attacked' | 'monster.damaged' | 'monster.died' | 'monster.despawned'

export type MonsterPayload = {
  monster: {
    id: string
    type: 'roaming_melee' | 'resource_guardian' | 'ruins_guardian'
    state: 'idle' | 'wandering' | 'aggro' | 'attacking' | 'dead'
    tile_x?: number
    tile_y?: number
    Tile?: { X: number; Y: number }
    health: number
    max_health?: number
    MaxHealth?: number
    damage: number
    aggro_radius?: number
    AggroRadius?: number
    target_id?: string
    TargetID?: string
    target_type?: string
    TargetType?: string
    updated_at?: string
    UpdatedAt?: string
  }
}
