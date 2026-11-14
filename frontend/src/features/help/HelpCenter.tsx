import { useEffect, useMemo, useState } from 'react'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { monsterCatalog } from '../../../../shared/catalog/monsters'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import { useGameStore } from '../../game/state/useGameStore'
import { Modal, SegmentedControl } from '../../shared/ui'
import { BookOpen } from '../../shared/ui/icons'
import { useAuthStore } from '../auth/useAuthStore'
import { buildCatalog, buildingLevelPreviewImage } from '../buildings/catalog'
import { defenseLevelStats, formatDamagePerSecond, isDefenseTrap, isDefenseWeapon } from '../buildings/defenseStats'
import { useInventory } from '../economy/useInventory'
import { ResourceIcon } from '../resources/ResourceIcon'

type HelpSection = 'buildings' | 'resources' | 'weapons' | 'monsters'
type BuildingCategory = (typeof buildingCatalog)[number]['category']
type Discovery = { buildings: string[]; buildingLevels: Record<string, number>; resources: string[]; weapons: string[]; monsters: string[] }

const sections = [
  { id: 'buildings', label: 'Постройки' },
  { id: 'resources', label: 'Ресурсы' },
  { id: 'weapons', label: 'Вооружение' },
  { id: 'monsters', label: 'Монстры' },
] as const

const emptyDiscovery: Discovery = { buildings: [], buildingLevels: {}, resources: [], weapons: [], monsters: [] }

export function HelpCenter() {
  const open = useGameStore((state) => state.uiPreferences.helpCenterOpen)
  const setOpen = useGameStore((state) => state.setHelpCenterOpen)
  const buildings = useGameStore((state) => state.buildings)
  const monsters = useGameStore((state) => state.monsters)
  const playerId = useAuthStore((state) => state.player?.id)
  const inventoryQuery = useInventory()
  const inventory = inventoryQuery.data?.inventory.items ?? []
  const [section, setSection] = useState<HelpSection>('buildings')
  const [buildingCategory, setBuildingCategory] = useState<BuildingCategory | 'all'>('all')
  const [discovery, setDiscovery] = useState<Discovery>(() => readDiscovery(playerId))

  useEffect(() => setDiscovery(readDiscovery(playerId)), [playerId])

  useEffect(() => {
    if (!playerId) return
    const owned = buildings.filter((building) => building.owner === playerId)
    const amounts = new Map(inventory.map((item) => [item.resource, item.amount]))
    const foundResources = resourceCatalog.filter((item) => item.category !== 'weapons' && (amounts.get(item.id) ?? 0) > 0).map((item) => item.id)
    const foundWeapons = resourceCatalog.filter((item) => item.category === 'weapons' && (amounts.get(item.id) ?? 0) > 0).map((item) => item.id)
    const buildingLevels = owned.reduce<Record<string, number>>((levels, building) => {
      levels[building.kind] = Math.max(levels[building.kind] ?? 0, building.level)
      return levels
    }, {})
    const next = mergeDiscovery(readDiscovery(playerId), {
      buildings: owned.map((building) => building.kind),
      buildingLevels,
      resources: foundResources,
      weapons: foundWeapons,
      monsters: monsters.map((monster) => monster.type),
    })
    if (sameDiscovery(next, discovery)) return
    setDiscovery(next)
    writeDiscovery(playerId, next)
  }, [buildings, inventory, monsters, playerId])

  const ownedBuildingLevels = useMemo(() => {
    const result = new Map<string, number>()
    for (const building of buildings) {
      if (building.owner !== playerId) continue
      result.set(building.kind, Math.max(result.get(building.kind) ?? 0, building.level))
    }
    return result
  }, [buildings, playerId])

  const ownedBuildEntries = buildCatalog.filter((item) => discovery.buildings.includes(item.kind))
  const buildingCategories = [...new Set(ownedBuildEntries.map((item) => item.category))]
  const visibleBuildEntries = buildingCategory === 'all'
    ? ownedBuildEntries
    : ownedBuildEntries.filter((item) => item.category === buildingCategory)
  const visibleResources = resourceCatalog.filter((item) => discovery.resources.includes(item.id))
  const visibleWeapons = resourceCatalog.filter((item) => item.category === 'weapons' && discovery.weapons.includes(item.id))
  const visibleMonsters = monsterCatalog.filter((item) => discovery.monsters.includes(item.type))

  return (
    <>
      <button type="button" className="help-center-launcher" aria-label="Открыть справку" title="Справка" onClick={() => setOpen(true)}>
        <BookOpen size={19} aria-hidden="true" />
      </button>
      <Modal title="Справка" open={open} onClose={() => setOpen(false)} className="help-center-modal">
        <div className="help-center-content">
          <SegmentedControl items={sections} value={section} label="Разделы справки" onChange={setSection} />
          {section === 'buildings' ? (
            <>
              <SegmentedControl
                items={[
                  { id: 'all', label: 'Все' },
                  ...buildingCategories.map((category) => ({ id: category, label: categoryLabel(category) })),
                ]}
                value={buildingCategory}
                label="Категории построек"
                onChange={setBuildingCategory}
              />
              <div className="help-card-grid">
              {visibleBuildEntries.map((entry) => {
                const spec = buildingCatalog.find((item) => item.type === entry.kind)
                const highestLevel = Math.max(discovery.buildingLevels[entry.kind] ?? 1, ownedBuildingLevels.get(entry.kind) ?? 1)
                const upgrades = (spec?.upgradeLevels ?? []).filter((upgrade) => upgrade.level <= highestLevel + 1)
                return (
                  <details className="help-card" key={entry.kind}>
                    <summary>
                      <strong>{entry.name}</strong>
                      <span>Уровень {highestLevel}</span>
                    </summary>
                    <p>{entry.description}</p>
                    <dl>
                      <div><dt>Размер</dt><dd>{entry.footprint.width} × {entry.footprint.height} клетки</dd></div>
                      <div><dt>Жители</dt><dd>{entry.population} <ResourceIcon id="population" label="Жители" iconVariant="asset" className="resident-icon-inline" decorative /></dd></div>
                      <div><dt>Здоровье</dt><dd>{spec?.health ?? '—'}</dd></div>
                      <div><dt>Время постройки</dt><dd>{entry.time}</dd></div>
                      <div><dt>Стоимость</dt><dd>{formatCost(entry.cost)}</dd></div>
                      {defenseLevelStats(entry.kind, highestLevel) ? <DefenseStatsList kind={entry.kind} level={highestLevel} population={spec?.upgradeLevels?.find((upgrade) => upgrade.level === highestLevel)?.population ?? entry.population} /> : null}
                    </dl>
                    {upgrades.length ? (
                      <div className="help-upgrades">
                        <h3>Открытые улучшения</h3>
                        {upgrades.map((upgrade) => (
                          <article key={upgrade.level}>
                            <img
                              className="help-upgrade-image"
                              src={buildingLevelPreviewImage(entry.kind, upgrade.level)}
                              alt={`${entry.name}, уровень ${upgrade.level}`}
                              loading="lazy"
                              decoding="async"
                            />
                            <div className="help-upgrade-details">
                              <strong>{entry.name}, уровень {upgrade.level}</strong>
                              <span>Здоровье: {upgrade.health} · жители: {upgrade.population} <ResourceIcon id="population" label="Жители" iconVariant="asset" className="resident-icon-inline" decorative /></span>
                              {isDefenseWeapon(entry.kind) ? (
                                <div className="help-upgrade-economy">
                                  <span>Время улучшения: {formatDuration(upgrade.buildSeconds)}</span>
                                  <span>Стоимость: {formatSharedCost(upgrade.cost)}</span>
                                </div>
                              ) : <>
                                <span>Время улучшения: {formatDuration(upgrade.buildSeconds)}</span>
                                <span>Стоимость: {formatSharedCost(upgrade.cost)}</span>
                              </>}
                              <DefenseStatsText kind={entry.kind} level={upgrade.level} population={upgrade.population} />
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : null}
                  </details>
                )
              })}
              {!ownedBuildEntries.length ? <p className="help-empty">Постройки появятся здесь после того, как вы возведете первую.</p> : null}
              </div>
            </>
          ) : null}
          {section === 'resources' ? (
            <div className="help-card-grid">
              {visibleResources.map((resource) => (
                <details className="help-card help-item-card" key={resource.id}>
                  <summary><ResourceIcon id={resource.id} label={resource.name} /><strong>{resource.name}</strong></summary>
                  <p>{resource.source ? `Источник: ${resource.source}.` : 'Игровой ресурс.'}</p>
                  <span>Категория: {categoryLabel(resource.category)} · хранение: {resource.hasLimit ? 'с лимитом' : 'без лимита'}</span>
                </details>
              ))}
              {!visibleResources.length ? <p className="help-empty">Ресурсы появятся здесь, когда вы впервые получите их.</p> : null}
            </div>
          ) : null}
          {section === 'weapons' ? (
            <div className="help-card-grid">
              {visibleWeapons.map((weapon) => (
                <details className="help-card help-item-card" key={weapon.id}>
                  <summary><ResourceIcon id={weapon.id} label={weapon.name} /><strong>{weapon.name}</strong></summary>
                  <p>{weapon.source ? `Производится или добывается: ${weapon.source}.` : 'Средство вооружения.'}</p>
                </details>
              ))}
              {!visibleWeapons.length ? <p className="help-empty">Вооружение появится здесь, когда вы впервые получите его.</p> : null}
            </div>
          ) : null}
          {section === 'monsters' ? (
            <div className="help-card-grid">
              {visibleMonsters.map((monster) => (
                <details className="help-card" key={monster.type}>
                  <summary><strong>{monster.name}</strong><span>Монстр</span></summary>
                  <p>Здоровье: {monster.maxHealth}. Урон: {monster.damage}. Скорость: {monster.speedTiles} кл./ход.</p>
                  <dl>
                    <div><dt>Дальность обнаружения</dt><dd>{monster.aggroRadius} клеток</dd></div>
                    <div><dt>Дальность атаки</dt><dd>{monster.attackRange} клеток</dd></div>
                    <div><dt>Монеты за победу</dt><dd>{monster.lootCoins}</dd></div>
                  </dl>
                </details>
              ))}
              {!visibleMonsters.length ? <p className="help-empty">Монстры появятся здесь после того, как вы встретите их на карте.</p> : null}
            </div>
          ) : null}
        </div>
      </Modal>
    </>
  )
}

function DefenseStatsList({ kind, level, population }: { kind: import('../../game/state/useGameStore').BuildingKind; level: number; population: number }) {
  const stats = defenseLevelStats(kind, level)
  if (!stats) return null
  if (isDefenseWeapon(kind)) return <>
    <div><dt>Урон за выстрел</dt><dd>{stats.damage}</dd></div>
    <div><dt>Урон/с</dt><dd>{formatDamagePerSecond(stats)}</dd></div>
    <div><dt>Перезарядка</dt><dd>{stats.cooldownSeconds} с.</dd></div>
    <div><dt>Радиус атаки</dt><dd>{stats.range} клетки</dd></div>
    <div><dt>Размер гарнизона</dt><dd>{population} <ResourceIcon id="population" label="Жители" iconVariant="asset" className="resident-icon-inline" decorative /></dd></div>
  </>
  return <>
    <div><dt>Урон</dt><dd>{stats.damage}</dd></div>
    <div><dt>Заряды</dt><dd>{stats.charges}</dd></div>
    <div><dt>Перезарядка</dt><dd>не требуется, срабатывает при входе</dd></div>
  </>
}

function DefenseStatsText({ kind, level, population }: { kind: import('../../game/state/useGameStore').BuildingKind; level: number; population: number }) {
  const stats = defenseLevelStats(kind, level)
  if (!stats) return null
  return isDefenseWeapon(kind) ? <span>Урон за выстрел: {stats.damage} · урон/с: {formatDamagePerSecond(stats)} · перезарядка: {stats.cooldownSeconds} с. · радиус атаки: {stats.range} кл. · гарнизон: {population} <ResourceIcon id="population" label="Жители" iconVariant="asset" className="resident-icon-inline" decorative /></span>
    : <span>Урон: {stats.damage} · заряды: {stats.charges} · перезарядка: не требуется, срабатывает при входе</span>
}

function readDiscovery(playerId?: string): Discovery {
  if (!playerId || typeof localStorage === 'undefined') return emptyDiscovery
  try {
    const value = localStorage.getItem(`real-city.help-discovery.${playerId}`)
    if (!value) return emptyDiscovery
    const parsed = JSON.parse(value) as Partial<Discovery>
    return {
      buildings: Array.isArray(parsed.buildings) ? parsed.buildings : [],
      buildingLevels: parsed.buildingLevels && typeof parsed.buildingLevels === 'object' ? parsed.buildingLevels : {},
      resources: Array.isArray(parsed.resources) ? parsed.resources : [],
      weapons: Array.isArray(parsed.weapons) ? parsed.weapons : [],
      monsters: Array.isArray(parsed.monsters) ? parsed.monsters : [],
    }
  } catch {
    return emptyDiscovery
  }
}

function writeDiscovery(playerId: string, value: Discovery) {
  try { localStorage.setItem(`real-city.help-discovery.${playerId}`, JSON.stringify(value)) } catch { /* Local progress remains available for this session. */ }
}

function mergeDiscovery(current: Discovery, found: Discovery): Discovery {
  return {
    buildings: [...new Set([...current.buildings, ...found.buildings])],
    buildingLevels: Object.fromEntries(Object.entries({ ...current.buildingLevels, ...found.buildingLevels }).map(([kind, level]) => [kind, Math.max(current.buildingLevels[kind] ?? 0, level)])),
    resources: [...new Set([...current.resources, ...found.resources])],
    weapons: [...new Set([...current.weapons, ...found.weapons])],
    monsters: [...new Set([...current.monsters, ...found.monsters])],
  }
}

function sameDiscovery(left: Discovery, right: Discovery) {
  const listsMatch = (['buildings', 'resources', 'weapons', 'monsters'] as const).every((key) => left[key].length === right[key].length && left[key].every((item) => right[key].includes(item)))
  const leftLevels = Object.entries(left.buildingLevels)
  return listsMatch && leftLevels.length === Object.keys(right.buildingLevels).length && leftLevels.every(([kind, level]) => right.buildingLevels[kind] === level)
}

function categoryLabel(category: string) {
  const labels: Record<string, string> = { center: 'Центр', housing: 'Жильё', fields: 'Поля и грядки', industry: 'Производство', defense: 'Оборона', roads: 'Дороги', storage: 'Хранилища', social: 'Союзы', trade: 'Торговля', basic: 'Базовый ресурс', raw: 'Сырьё', crafted: 'Производство', rare: 'Редкий ресурс', fuel: 'Топливо', weapons: 'Вооружение' }
  return labels[category] ?? category
}

function formatCost(cost: readonly { label: string; amount: number }[]) {
  return cost.length ? cost.map((item) => `${item.label} — ${item.amount}`).join(', ') : 'Бесплатно'
}

function formatSharedCost(cost: readonly { resource: string; amount: number }[]) {
  return cost.length ? cost.map((item) => `${resourceCatalog.find((resource) => resource.id === item.resource)?.name ?? item.resource} — ${item.amount}`).join(', ') : 'Бесплатно'
}

function formatDuration(seconds: number) {
  if (seconds <= 0) return 'мгновенно'
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return remainder ? `${minutes} мин. ${remainder} сек.` : `${minutes} мин.`
}
