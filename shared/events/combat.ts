export type CombatRecord = {
  id: string
  attacker_id: string
  owner_id: string
  building_id: string
  building_type: string
  level: number
  damage: number
  destroyed: boolean
  xp: number
  base_xp: number
  source: string
  created_at: string
}
