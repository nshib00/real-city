import type { MonsterEntity } from '../state/useGameStore'
import { monsterDisplayName } from './monsterAssetRegistry'

export function monsterClassName(monster: MonsterEntity) {
  return `map-monster map-monster-${monster.type} map-monster-${monster.state}`
}

export function monsterLabel(monster: MonsterEntity) {
  return `${monsterDisplayName(monster.type)} · ${monster.health}/${monster.maxHealth}`
}
