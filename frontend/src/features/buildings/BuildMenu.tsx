import { Building2, Check, Clock, UsersRound, X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { useGameStore } from '../../game/state/useGameStore'
import { placeBuilding as placeBuildingRequest, toPlacedBuilding } from '../../shared/api/buildings'
import { ApiClientError } from '../../shared/api/client'
import { IconButton } from '../../shared/ui'
import { validatePlacementPreview } from '../build-placement/placement'
import { inventoryAmount, useInventory } from '../economy/useInventory'
import { ResourceIcon } from '../resources/ResourceIcon'
import { buildCatalog } from './catalog'

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

export function BuildMenu() {
  const [pendingKind, setPendingKind] = useState<string | null>(null)
  const [buildError, setBuildError] = useState('')
  const [category, setCategory] = useState<BuildCategory>('all')
  const open = useGameStore((state) => state.uiPreferences.buildMenuOpen)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const buildings = useGameStore((state) => state.buildings)
  const monsters = useGameStore((state) => state.monsters)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const queryClient = useQueryClient()
  const inventoryQuery = useInventory()
  const inventory = inventoryQuery.data?.inventory.items
  const hasTownHall = buildings.some((building) => building.kind === 'town_hall')
  const selectedWorldTile = selectedTile ? worldTiles.find((tile) => tile.x === selectedTile.x && tile.y === selectedTile.y) ?? null : null
  const visibleCatalog = category === 'all' ? buildCatalog : buildCatalog.filter((item) => item.category === category)

  if (!open) {
    return null
  }

  return (
    <div className="build-menu-backdrop" role="presentation">
      <section className="build-menu" aria-label="Меню строительства">
        <header>
          <div>
            <h2>Стройка</h2>
            <span>{selectedTile ? `тайл ${selectedTile.x}:${selectedTile.y}` : 'выберите тайл'}</span>
          </div>
          <IconButton label="Закрыть меню строительства" icon={X} onClick={() => setBuildMenuOpen(false)} />
        </header>
        <div className="build-category-tabs" role="tablist" aria-label="Категории построек">
          {categories.map((item) => (
            <button className={category === item.id ? 'build-category-tab build-category-tab-active' : 'build-category-tab'} key={item.id} type="button" role="tab" aria-selected={category === item.id} onClick={() => setCategory(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <div className="build-list">
          {visibleCatalog.map((item) => {
            const lockedByTownHall = item.kind !== 'town_hall' && !hasTownHall
            const lockedTownHall = item.kind === 'town_hall' && hasTownHall
            const placement = validatePlacementPreview({ kind: item.kind, tile: selectedTile, terrain: selectedWorldTile?.terrain, footprint: item.footprint, worldTiles, buildings, monsters })
            const shortage = getShortage(item, inventory)
            const disabled = !placement.valid || lockedByTownHall || lockedTownHall || shortage !== null
            return (
              <article className={disabled ? 'build-card build-card-disabled' : 'build-card'} key={item.kind}>
                <div className={`build-image build-icon-${item.kind}`} aria-hidden="true">
                  <Building2 size={22} />
                </div>
                <div className="build-card-body">
                  <strong>{item.name}</strong>
                  <span>{getBuildHint({ placementReason: placement.reason, lockedByTownHall, lockedTownHall, shortage, fallback: item.description })}</span>
                  <small>
                    <Clock size={13} aria-hidden="true" /> {item.time}
                    <UsersRound size={13} aria-hidden="true" /> {item.population}
                  </small>
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
                <IconButton
                  label={`Построить ${item.name}`}
                  icon={Check}
                  disabled={disabled || pendingKind === item.kind}
                  onClick={async () => {
                    if (!selectedTile) {
                      return
                    }
                    setPendingKind(item.kind)
                    setBuildError('')
                    try {
                      const result = await placeBuildingRequest({ type: item.kind, tile_x: selectedTile.x, tile_y: selectedTile.y })
                      addBuilding(toPlacedBuilding(result.building))
                      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
                      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
                    } catch (error) {
                      setBuildError(formatBuildError(error))
                      return
                    } finally {
                      setPendingKind(null)
                    }
                  }}
                />
              </article>
            )
          })}
        </div>
        {buildError ? <p className="build-error" role="alert">{buildError}</p> : null}
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

function getShortage(item: (typeof buildCatalog)[number], inventory: { resource: string; amount: number }[] | undefined) {
  if (!inventory) {
    return null
  }
  if (item.population > 0 && item.time !== 'мгновенно' && inventoryAmount(inventory, 'population') < item.population) {
    return `Не хватает свободного населения: нужно ${item.population}, доступно ${inventoryAmount(inventory, 'population')}`
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
  }
  return labels[resource] ?? resource
}
