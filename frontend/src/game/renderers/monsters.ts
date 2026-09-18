import type { MonsterEntity } from '../state/useGameStore'

export function monsterClassName(monster: MonsterEntity) {
  return `map-monster map-monster-${monster.type} map-monster-${monster.state}`
}

export function monsterLabel(monster: MonsterEntity) {
  const names: Record<MonsterEntity['type'], string> = {
    roaming_melee: 'Бродячий налетчик',
    resource_guardian: 'Страж залежи',
    ruins_guardian: 'Сторож руин',
  }
  return `${names[monster.type]} · ${monster.health}/${monster.maxHealth}`
}
