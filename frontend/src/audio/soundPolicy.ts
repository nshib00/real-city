import { spatialSound } from './spatialAudio'

export type SoundTile = { x: number; y: number }

export function combatDistanceGain(tile: SoundTile | undefined, center: SoundTile, radiusChunks: number): number {
  return spatialSound(tile, center, radiusChunks).gain
}

export function weaponSound(type: string): 'combat.weapon.cannon' | 'combat.weapon.tower' | 'combat.weapon.bolt_thrower' | 'combat.weapon.storm_coil' {
  if (type === 'defense_bolt_thrower') return 'combat.weapon.bolt_thrower'
  if (type === 'defense_storm_coil') return 'combat.weapon.storm_coil'
  if (type === 'defense_cannon') return 'combat.weapon.cannon'
  return 'combat.weapon.tower'
}

export function defenseSound(type: string): 'combat.defense.stakes' | 'combat.defense.resin_snare' | 'combat.defense.guardian_enclosure' | 'combat.defense.automaton_bay' | null {
  switch (type) {
    case 'defense_stakes': return 'combat.defense.stakes'
    case 'defense_resin_snare': return 'combat.defense.resin_snare'
    case 'defense_guardian_enclosure': return 'combat.defense.guardian_enclosure'
    case 'defense_automaton_bay': return 'combat.defense.automaton_bay'
    default: return null
  }
}

export function buildingImpactSound(type: string): 'combat.impact.wood' | 'combat.impact.stone' {
  return type.includes('wood') || type.includes('lumber') || type.includes('farm') || type.includes('field')
    ? 'combat.impact.wood' : 'combat.impact.stone'
}
