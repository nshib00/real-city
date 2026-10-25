const fuseSeconds: Record<string, number> = {
  throwing_knives: 0,
  hunting_traps: 15,
  blackpowder_bomb: 40,
  firebomb: 120,
  shaped_charge: 300,
  shock_charge: 900,
  siege_mine: 1200,
  breach_bomb: 1800,
  resonance_charge: 2700,
}

export function weaponFuseLabel(id: string) {
  const seconds = fuseSeconds[id]
  if (seconds === undefined) return 'время неизвестно'
  if (seconds === 0) return 'мгновенно'
  if (seconds < 60) return `через ${seconds} с`
  return `через ${seconds / 60} мин`
}
