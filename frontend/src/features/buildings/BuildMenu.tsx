import { Building2, Check, ChevronLeft, ChevronRight, Clock, Eye, X } from '../../shared/ui/icons'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { playUiSound } from '../../audio/playUiSound'
import { cellLabel } from '../../game/coordinates/district'
import { useGameStore } from '../../game/state/useGameStore'
import { placeBuilding as placeBuildingRequest, toPlacedBuilding } from '../../shared/api/buildings'
import { ApiClientError } from '../../shared/api/client'
import { IconButton } from '../../shared/ui'
import { ActionState } from '../../shared/ui/ActionState'
import { AeolianIcon } from '../../shared/ui/AeolianIcon'
import { useAuthStore } from '../auth/useAuthStore'
import { validatePlacementPreview } from '../build-placement/placement'
import { availablePopulation, inventoryAmount, useInventory } from '../economy/useInventory'
import { ResourceIcon } from '../resources/ResourceIcon'
import { showToast } from '../notifications/toast'
import { buildCatalog } from './catalog'
import { placementMaterialVariant, placementSound, playBuildingSound } from './buildingAudio'

type BuildCategory = (typeof categories)[number]['id']

const categories = [
  { id: 'all', label: 'Все' },
  { id: 'housing', label: 'Жилье' },
  { id: 'fields', label: 'Грядки' },
  { id: 'industry', label: 'Заводы' },
  { id: 'defense', label: 'Оборона' },
  { id: 'storage', label: 'Склады' },
  { id: 'trade', label: 'Торговля' },
  { id: 'roads', label: 'Дороги' },
  { id: 'center', label: 'Центр' },
  { id: 'social', label: 'Союзы' },
] as const
const categoryIcons: Record<BuildCategory, string> = { all: 'build', housing: 'housing', fields: 'fields', industry: 'production', defense: 'shield', storage: 'storage', trade: 'market', roads: 'road', center: 'center', social: 'alliance' }

export function BuildMenu() {
  const [pendingKind, setPendingKind] = useState<string | null>(null)
  const [buildError, setBuildError] = useState('')
  const [category, setCategory] = useState<BuildCategory>('all')
  const [search, setSearch] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const open = useGameStore((state) => state.uiPreferences.buildMenuOpen)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const placementPreviewKind = useGameStore((state) => state.placementPreviewKind)
  const setPlacementPreviewKind = useGameStore((state) => state.setPlacementPreviewKind)
  const buildings = useGameStore((state) => state.buildings)
  const monsters = useGameStore((state) => state.monsters)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const player = useAuthStore((state) => state.player)
  const queryClient = useQueryClient()
  const inventoryQuery = useInventory()
  const inventory = inventoryQuery.data?.inventory.items
  const ownerBuildings = useMemo(() => (player ? buildings.filter((building) => building.owner === player.id) : buildings), [buildings, player])
  const freePopulation = availablePopulation(inventory)
  const hasTownHall = useMemo(() => ownerBuildings.some((building) => building.kind === 'town_hall'), [ownerBuildings])
  const worldTileByKey = useMemo(() => new Map(worldTiles.map((tile) => [`${tile.x}:${tile.y}`, tile])), [worldTiles])
  const selectedWorldTile = selectedTile ? worldTileByKey.get(`${selectedTile.x}:${selectedTile.y}`) ?? null : null
  const isOilWellTile = selectedWorldTile?.terrain === 'oil_well'
  const categoryCatalog = useMemo(
    () => sortBuildCatalogByCoinCost(buildCatalog.filter((item) => isOilWellTile ? item.kind === 'oil_well' : item.kind !== 'oil_well' && (category === 'all' || item.category === category))),
    [category, isOilWellTile],
  )
  const visibleCatalog = categoryCatalog.filter((item) => {
    if (!`${item.name} ${item.description}`.toLocaleLowerCase('ru').includes(search.trim().toLocaleLowerCase('ru'))) return false
    if (!availableOnly) return true
    return (Boolean(inventory) || Boolean(item.free)) && !(item.kind !== 'town_hall' && !hasTownHall) && !(item.kind === 'town_hall' && hasTownHall)
      && !getShortage(item, inventory, freePopulation)
      && validatePlacementPreview({ kind: item.kind, tile: selectedTile, terrain: selectedWorldTile?.terrain, footprint: item.footprint, worldTiles, buildings, ownerId: player?.id, monsters }).valid
  })

  useEffect(() => {
    if (!open) setCollapsed(false)
  }, [open])

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    document.getElementById('game-build-menu')?.focus()
    return () => { if (previous?.isConnected) previous.focus() }
  }, [open])

  useEffect(() => {
    if (!open || !placementPreviewKind) return
    const cancelOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      playUiSound('ui.place.cancel')
      setPlacementPreviewKind(null)
    }
    window.addEventListener('keydown', cancelOnEscape)
    return () => window.removeEventListener('keydown', cancelOnEscape)
  }, [open, placementPreviewKind, setPlacementPreviewKind])

  if (!open) {
    return null
  }

  return (
    <div className={collapsed ? 'build-menu-backdrop build-menu-backdrop-collapsed' : 'build-menu-backdrop'} role="presentation">
      <section id="game-build-menu" tabIndex={-1} onKeyDown={(event) => { if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); setBuildMenuOpen(false); document.getElementById('game-tools')?.focus() } }} className={`build-menu${isOilWellTile ? ' build-menu-oil-well' : ''}${collapsed ? ' build-menu-collapsed' : ''}`} aria-label="Меню строительства">
        <header>
          <div>
            <h2>{isOilWellTile ? 'Нефтяная вышка' : 'Стройка'}</h2>
            {!collapsed ? <span>{selectedTile ? `клетка ${cellLabel(selectedTile)}` : 'выберите клетку'}</span> : null}
          </div>
          <div className="build-menu-header-actions">
            {placementPreviewKind ? <IconButton label="Отменить предпросмотр постройки" icon={X} sound="ui.place.cancel" onClick={() => setPlacementPreviewKind(null)} /> : null}
            <IconButton label={collapsed ? 'Развернуть меню строительства' : 'Свернуть меню строительства'} icon={collapsed ? ChevronLeft : ChevronRight} sound={collapsed ? 'ui.toggle.on' : 'ui.toggle.off'} onClick={() => setCollapsed(!collapsed)} />
            <IconButton label="Закрыть меню строительства" icon={X} sound={placementPreviewKind ? 'ui.place.cancel' : 'ui.panel.close'} onClick={() => setBuildMenuOpen(false)} />
          </div>
        </header>
        {!collapsed && !isOilWellTile ? <div className="build-category-tabs" role="group" aria-label="Категории построек">
          {categories.map((item) => (
            <button className={category === item.id ? 'build-category-tab build-category-tab-active' : 'build-category-tab'} key={item.id} type="button" aria-pressed={category === item.id} data-audio-handled="true" onClick={() => { if (category !== item.id) { playUiSound('ui.tab'); setCategory(item.id) } }}>
              <AeolianIcon name={categoryIcons[item.id]} size={16} /> {item.label}
            </button>
          ))}
        </div> : null}
        {!collapsed ? <div className="build-filters">
          <label>Поиск построек<input type="search" value={search} onChange={(event) => setSearch(event.target.value)} /></label>
          <label><input type="checkbox" checked={availableOnly} onChange={(event) => setAvailableOnly(event.target.checked)} /> Только доступные здесь</label>
          <small role="status">Найдено: {visibleCatalog.length}{!inventory ? ' · проверяем запасы' : ''}</small>
          {inventoryQuery.error ? <button type="button" onClick={() => void inventoryQuery.refetch()}>Повторить загрузку запасов</button> : null}
        </div> : null}
        {!collapsed ? <div className="build-list">
          {!visibleCatalog.length ? <p>Нет подходящих построек. Измените категорию, поиск или фильтр доступности.</p> : null}
          {visibleCatalog.map((item) => {
            const lockedByTownHall = item.kind !== 'town_hall' && !hasTownHall
            const lockedTownHall = item.kind === 'town_hall' && hasTownHall
            const placement = validatePlacementPreview({ kind: item.kind, tile: selectedTile, terrain: selectedWorldTile?.terrain, footprint: item.footprint, worldTiles, buildings, ownerId: player?.id, monsters })
            const shortage = getShortage(item, inventory, freePopulation)
            const disabled = (!inventory && !item.free) || !placement.valid || lockedByTownHall || lockedTownHall || shortage !== null
            return (
              <article className={`${disabled ? 'build-card build-card-disabled' : 'build-card'}${placementPreviewKind === item.kind ? ' build-card-preview' : ''}`} key={item.kind}>
                <div className={`build-image build-icon-${item.kind}`} aria-hidden="true">
                  {item.previewImage ? <img src={item.previewImage} alt="" draggable={false} loading="lazy" decoding="async" /> : <Building2 size={22} />}
                </div>
                <div className="build-card-body">
                  <strong>{item.name}</strong>
                  <span>{getBuildHint({ placementReason: placement.reason, lockedByTownHall, lockedTownHall, shortage, fallback: item.description })}</span>
                  <small>
                    <Clock size={13} aria-hidden="true" /> {item.time}
                    <span className="build-card-population">{item.population} <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /></span>
                  </small>
                  {!inventory && !item.free ? <small role="status">{inventoryQuery.error ? 'Запасы не загружены. Повторите загрузку.' : 'Проверяем запасы…'}</small> : null}
                  <em className="build-cost">
                    {item.free
                      ? 'бесплатно'
                      : item.cost.map((cost) => (
                          <span key={`${item.kind}:${cost.resource}`} title={`${cost.label}: ${cost.amount}`}>
                            <ResourceIcon id={cost.resource} label={cost.label} />
                            {cost.amount}
                          </span>
                        ))}
                  </em>
                </div>
                <div className="build-card-actions">
                  <IconButton
                    label={`Предпросмотр ${item.name} на карте`}
                    icon={Eye}
                    sound="ui.place.preview"
                    onClick={() => { setPlacementPreviewKind(item.kind); setCollapsed(true) }}
                  />
                <IconButton
                  label={`Построить ${item.name}`}
                  icon={Check}
                  disabled={disabled || pendingKind !== null}
                  loading={pendingKind === item.kind}
                  onClick={async () => {
                    if (!selectedTile) {
                      return
                    }
                    setPendingKind(item.kind)
                    setBuildError('')
                    const actorId = player?.id
                    try {
                      const result = await placeBuildingRequest({ type: item.kind, tile_x: selectedTile.x, tile_y: selectedTile.y })
                      if (useAuthStore.getState().player?.id !== actorId) return
                      playBuildingSound(placementSound(result.building.type, result.building.state), result.building.id, 'placed', 1200, placementMaterialVariant(result.building.type))
                      if (item.cost.some((cost) => cost.resource === 'coins' && cost.amount > 0)) playUiSound('economy.coin.spent')
                      showToast('info', 'Строительство началось')
                      addBuilding(toPlacedBuilding(result.building))
                      setBuildMenuOpen(false)
                      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
                      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
                    } catch (error) {
                      if (useAuthStore.getState().player?.id !== actorId) return
                      playUiSound(error instanceof ApiClientError && error.apiError.fields?.coins ? 'economy.coin.insufficient'
                        : error instanceof ApiClientError && Object.keys(error.apiError.fields ?? {}).some((field) => field !== 'tile' && field !== 'terrain' && field !== 'limit') ? 'ui.resource.insufficient' : 'ui.action.invalid')
                      setBuildError(formatBuildError(error))
                      return
                    } finally {
                      setPendingKind(null)
                    }
                  }}
                />
                </div>
              </article>
            )
          })}
        </div> : null}
        {pendingKind ? <ActionState phase="pending" reason="Проверяем размещение и стоимость на сервере. Запасы обновятся после подтверждения." /> : null}
        {!collapsed && buildError ? <p className="build-error" role="alert">{buildError}</p> : null}
      </section>
    </div>
  )
}

function getBuildHint(input: { placementReason: string | null; lockedByTownHall: boolean; lockedTownHall: boolean; shortage: string | null; fallback: string }) {
  if (input.lockedByTownHall) {
    return 'Сначала постройте ратушу.'
  }
  if (input.lockedTownHall) {
    return 'Ратуша уже построена.'
  }
  if (input.placementReason) {
    return input.placementReason
  }
  if (input.shortage) {
    return input.shortage
  }
  return input.fallback
}

function sortBuildCatalogByCoinCost(items: readonly (typeof buildCatalog)[number][]) {
  return [...items].sort((left, right) => {
    const costDiff = coinCost(left) - coinCost(right)
    if (costDiff !== 0) {
      return costDiff
    }
    return left.name.localeCompare(right.name, 'ru')
  })
}

function coinCost(item: (typeof buildCatalog)[number]) {
  if (item.free) {
    return 0
  }
  return item.cost.find((cost) => cost.resource === 'coins')?.amount ?? Number.POSITIVE_INFINITY
}

function getShortage(item: (typeof buildCatalog)[number], inventory: { resource: string; amount: number }[] | undefined, freePopulation: number) {
  if (!inventory) {
    return null
  }
  if (item.population > 0 && item.time !== 'мгновенно' && freePopulation < item.population) {
    return `Не хватает свободного населения: нужно ${item.population}, доступно ${freePopulation}`
  }
  const missing = item.cost.find((cost) => inventoryAmount(inventory, cost.resource) < cost.amount)
  if (missing) {
    return `Не хватает ресурса: ${missing.label} ${inventoryAmount(inventory, missing.resource)}/${missing.amount}`
  }
  return null
}

function formatBuildError(error: unknown) {
  if (error instanceof ApiClientError) {
    const fields = error.apiError.fields ?? {}
    if (fields.population) {
      return `Не хватает свободного населения: ${fields.population}`
    }
    const missing = Object.entries(fields)
      .filter(([resource]) => resource !== 'tile' && resource !== 'terrain' && resource !== 'limit')
      .map(([resource, value]) => `${resourceLabel(resource)} (${value})`)
    if (missing.length > 0) {
      return `Не хватает ресурсов: ${missing.join(', ')}`
    }
    if (fields.limit) {
      return `${error.message}: ${fields.limit}`
    }
    if (fields.tile) {
      return `${error.message}: ${fields.tile}`
    }
    return error.message
  }
  return error instanceof Error ? error.message : 'Не удалось начать строительство'
}

function resourceLabel(resource: string) {
  const labels: Record<string, string> = {
    population: 'население',
    coins: 'монеты',
    wood: 'древесина',
    stone: 'камень',
    brick: 'кирпич',
    flax: 'лен',
    planks: 'доски',
    premium_planks: 'премиум-доски',
    copper_parts: 'медные детали',
    rope: 'веревки',
    iron_ingot: 'железные слитки',
    gold_ingot: 'золотые слитки',
    mushrooms: 'грибы',
    'super-mushrooms': 'супер-грибы',
    'super-windleaf': 'супер-ветролист',
    emerald_dust: 'изумрудная пыль',
    metal: 'металл',
    glass: 'стекло',
    concrete: 'бетон',
    steel: 'сталь',
    electronics: 'электроника',
    windleaf: 'ветролист',
    clay: 'глина',
    coal: 'уголь',
    sand: 'песок',
    iron_ore: 'железная руда',
    copper: 'медь',
    mechanism: 'механизмы',
    super_mechanism: 'супер-механизмы',
    reinforced_concrete: 'железобетон',
    reinforced_beams: 'усиленные балки',
    armor_plates: 'защитные пластины',
    fabric: 'ткань',
    herbs: 'травы',
    tools: 'инструменты',
    star_glass: 'звездное стекло',
    light_crystal: 'светокристалл',
  }
  return labels[resource] ?? resource
}
