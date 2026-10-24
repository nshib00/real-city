/** Словарь звуковых намерений. Файлы и воспроизведение добавляются в следующих фазах. */
export const soundEvents = {
  ui: {
    bus: 'ui', priority: 'normal', ids: [
      'ui.click', 'ui.tab', 'ui.toggle.on', 'ui.toggle.off', 'ui.panel.open', 'ui.panel.close',
      'ui.dialog.open', 'ui.select.tile', 'ui.select.building', 'ui.select.monster',
      'ui.place.preview', 'ui.place.rotate', 'ui.place.cancel', 'ui.action.invalid',
      'ui.resource.insufficient', 'ui.confirm', 'ui.cancel', 'ui.toast.info',
      'ui.toast.warning', 'ui.toast.error',
    ],
  },
  economy: {
    bus: 'ui', priority: 'normal', ids: [
      'economy.coin.earned', 'economy.coin.spent', 'economy.coin.insufficient',
      'economy.harvest.field', 'economy.crop.ready', 'economy.crop.expired',
      'economy.gather.wood', 'economy.gather.stone', 'economy.gather.ore',
      'economy.gather.clay', 'economy.gather.sand', 'economy.gather.oil',
      'economy.gather.resin', 'economy.gather.crystal', 'economy.gather.rare',
      'economy.node.claimed', 'economy.node.depleted', 'economy.node.respawned',
      'economy.production.started', 'economy.production.ready', 'economy.production.collected',
      'economy.storage.deposit', 'economy.storage.withdraw', 'economy.storage.full',
      'economy.market.listed', 'economy.market.bought', 'economy.market.sold',
      'economy.market.cancelled', 'economy.level.up', 'economy.reward.rare',
    ],
  },
  build: {
    bus: 'world', priority: 'normal', ids: [
      'build.placed', 'build.started', 'build.completed', 'build.upgrade.started',
      'build.upgrade.completed', 'build.rushed', 'build.repair.started', 'build.repaired',
      'build.cancelled', 'build.road.placed', 'build.wall.placed', 'build.damaged.light',
      'build.damaged.heavy', 'build.damaged.ruined', 'build.demolished',
    ],
  },
  world: {
    bus: 'world', priority: 'low', ids: [
      'world.forest.explore', 'world.forest.cut', 'world.ruin.discovered',
      'world.ruin.captured', 'world.territory.claimed', 'world.resource.discovered',
    ],
  },
  combat: {
    bus: 'world', priority: 'high', ids: [
      'combat.weapon.cannon', 'combat.impact.stone', 'combat.impact.wood',
      'combat.impact.flesh', 'combat.weapon.tower', 'combat.weapon.bolt_thrower',
      'combat.weapon.storm_coil', 'combat.defense.stakes', 'combat.defense.resin_snare',
      'combat.defense.guardian_enclosure', 'combat.defense.automaton_bay',
      'combat.monster.aggro', 'combat.monster.attack', 'combat.monster.hit',
      'combat.monster.death', 'combat.monster.step', 'combat.monster.idle',
      'combat.player.attack', 'combat.player.hit', 'combat.loot.dropped',
      'combat.loot.claimed', 'combat.threat.nearby', 'combat.raid.started',
      'combat.victory', 'combat.retreat',
    ],
  },
  social: {
    bus: 'ui', priority: 'normal', ids: [
      'social.chat.received', 'social.chat.sent', 'social.chat.mention',
      'social.alliance.invite', 'social.alliance.accepted', 'social.alliance.declined',
      'social.alliance.treasury',
    ],
  },
  ambience: {
    bus: 'ambience', priority: 'low', ids: [
      'ambience.grass', 'ambience.forest', 'ambience.river', 'ambience.mountain',
      'ambience.ruins', 'ambience.town', 'ambience.workshop', 'ambience.field',
      'ambience.oil_well',
    ],
  },
} as const

export type SoundFamily = keyof typeof soundEvents
export type SoundId = (typeof soundEvents)[SoundFamily]['ids'][number]
export type SoundBus = 'ui' | 'world' | 'alerts' | 'ambience'
export type SoundPriority = 'critical' | 'high' | 'normal' | 'low'

/** Исключения из настроек семейства. Применять при сборке manifest. */
export const soundEventOverrides: Partial<Record<SoundId, { bus?: SoundBus; priority?: SoundPriority }>> = {
  'ui.action.invalid': { priority: 'high' },
  'ui.resource.insufficient': { priority: 'high' },
  'ui.toast.warning': { bus: 'alerts', priority: 'high' },
  'ui.toast.error': { bus: 'alerts', priority: 'high' },
  'economy.coin.insufficient': { priority: 'high' },
  'economy.harvest.field': { bus: 'world' },
  'economy.gather.wood': { bus: 'world' },
  'economy.gather.stone': { bus: 'world' },
  'economy.gather.ore': { bus: 'world' },
  'economy.gather.clay': { bus: 'world' },
  'economy.gather.sand': { bus: 'world' },
  'economy.gather.oil': { bus: 'world' },
  'economy.gather.resin': { bus: 'world' },
  'economy.gather.crystal': { bus: 'world' },
  'economy.gather.rare': { bus: 'world', priority: 'high' },
  'economy.node.claimed': { bus: 'world' },
  'economy.node.depleted': { bus: 'world' },
  'economy.node.respawned': { bus: 'world' },
  'economy.level.up': { priority: 'high' },
  'economy.reward.rare': { priority: 'high' },
  'build.completed': { priority: 'high' },
  'build.damaged.ruined': { bus: 'alerts', priority: 'critical' },
  'combat.monster.step': { priority: 'low' },
  'combat.monster.idle': { priority: 'low' },
  'combat.threat.nearby': { bus: 'alerts', priority: 'critical' },
  'combat.raid.started': { bus: 'alerts', priority: 'critical' },
  'social.chat.mention': { bus: 'alerts', priority: 'high' },
  'social.alliance.invite': { bus: 'alerts', priority: 'high' },
}
