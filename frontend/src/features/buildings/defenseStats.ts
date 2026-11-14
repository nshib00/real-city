import type { BuildingKind } from '../../game/state/useGameStore'

export type DefenseLevelStats = {
  damage: number
  range?: number
  cooldownSeconds?: number
  charges?: number
}

const weaponStats: Partial<Record<BuildingKind, DefenseLevelStats[]>> = {
  defense_bolt_thrower: [
    { range: 2, damage: 6, cooldownSeconds: 2 }, { range: 2, damage: 8, cooldownSeconds: 2 },
    { range: 3, damage: 10, cooldownSeconds: 2 }, { range: 3, damage: 12, cooldownSeconds: 2 },
    { range: 3, damage: 15, cooldownSeconds: 2 }, { range: 4, damage: 18, cooldownSeconds: 2 },
    { range: 4, damage: 21, cooldownSeconds: 2 }, { range: 4, damage: 25, cooldownSeconds: 2 },
  ],
  defense_cannon: [
    { range: 2, damage: 18, cooldownSeconds: 8 }, { range: 2, damage: 23, cooldownSeconds: 8 },
    { range: 3, damage: 27, cooldownSeconds: 8 }, { range: 3, damage: 33, cooldownSeconds: 8 },
    { range: 3, damage: 41, cooldownSeconds: 8 }, { range: 4, damage: 49, cooldownSeconds: 8 },
    { range: 4, damage: 60, cooldownSeconds: 8 }, { range: 4, damage: 72, cooldownSeconds: 8 },
    { range: 5, damage: 85, cooldownSeconds: 8 }, { range: 5, damage: 100, cooldownSeconds: 8 },
    { range: 5, damage: 117, cooldownSeconds: 8 }, { range: 6, damage: 137, cooldownSeconds: 8 },
  ],
  defense_storm_coil: [
    { range: 2, damage: 30, cooldownSeconds: 20 }, { range: 2, damage: 38, cooldownSeconds: 20 },
    { range: 3, damage: 48, cooldownSeconds: 20 }, { range: 3, damage: 60, cooldownSeconds: 20 },
    { range: 3, damage: 73, cooldownSeconds: 20 }, { range: 3, damage: 88, cooldownSeconds: 20 },
  ],
}

const trapStats: Partial<Record<BuildingKind, DefenseLevelStats[]>> = {
  defense_stakes: [25, 32, 42, 55, 70, 90].map((damage) => ({ damage, charges: 3 })),
  defense_resin_snare: [12, 18, 26, 36].map((damage) => ({ damage, charges: 2 })),
}

export function defenseLevelStats(kind: BuildingKind, level: number): DefenseLevelStats | undefined {
  const stats = weaponStats[kind] ?? trapStats[kind]
  return stats?.[level - 1]
}

export function isDefenseWeapon(kind: BuildingKind) {
  return Boolean(weaponStats[kind])
}

export function isDefenseTrap(kind: BuildingKind) {
  return Boolean(trapStats[kind])
}

export function damagePerSecond(stats: DefenseLevelStats) {
  return stats.cooldownSeconds ? stats.damage / stats.cooldownSeconds : undefined
}

export function formatDamagePerSecond(stats: DefenseLevelStats) {
  const value = damagePerSecond(stats)
  return value === undefined ? '—' : Number.isInteger(value) ? String(value) : value.toFixed(1).replace('.', ',')
}
