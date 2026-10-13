import { useEffect, useState } from 'react'
import { Box, Gem, Hammer, Route, Sprout, Swords, Trash2, TrendingUp } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { tileToChunk } from '../../game/coordinates/iso'
import { BuildingModelPreview } from '../../game/renderers/BuildingModelPreview'
import { canResolveBuildingModelAsset } from '../../game/renderers/buildingRegistry'
import { buildingSpriteAsset } from '../../game/renderers/buildingSpriteAssets'
import { useGameStore, type BuildingKind, type PlacedBuilding } from '../../game/state/useGameStore'
import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { deleteBuilding as deleteBuildingRequest, patchBuilding, toPlacedBuilding } from '../../shared/api/buildings'
import { ApiClientError } from '../../shared/api/client'
import { advanceField, harvestField } from '../../shared/api/economy'
import { attackMonster, toMonster } from '../../shared/api/monsters'
import { IconButton, Modal, SegmentedControl, Tabs } from '../../shared/ui'
import { useAuthStore } from '../auth/useAuthStore'
import { inventoryAmount, useInventory } from '../economy/useInventory'
import { fieldCropSpec } from '../fields/fieldGrowth'
import { ResourceIcon } from '../resources/ResourceIcon'
import { useThreatLevel } from '../threat/ThreatPanel'

type InspectorTab = 'tile' | 'object' | 'player'

const tabs = [
  { id: 'tile', label: 'Тайл' },
  { id: 'object', label: 'Объект' },
  { id: 'player', label: 'Игрок' },
] as const

const claimModes = [
  { id: 'build', label: 'Стройка' },
  { id: 'raid', label: 'Рейд' },
] as const

export function Inspector() {
  const [activeTab, setActiveTab] = useState<InspectorTab>('tile')
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [modelPreviewOpen, setModelPreviewOpen] = useState(false)
  const [upgradeError, setUpgradeError] = useState('')
  const [constructionError, setConstructionError] = useState('')
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const tool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const upsertMonster = useGameStore((state) => state.upsertMonster)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const queryClient = useQueryClient()
  const inventoryQuery = useInventory()
  const activeTile = selectedTile ?? hoveredTile
  const chunk = activeTile ? tileToChunk(activeTile) : null
  const selectedBuilding = buildings.find((building) => building.id === selectedBuildingId) ?? null
  const player = useAuthStore((state) => state.player)
  const canManageSelectedBuilding = Boolean(selectedBuilding && player && selectedBuilding.owner === player.id)
  const selectedMonster = useGameStore((state) => state.monsters.find((monster) => monster.id === selectedMonsterId) ?? null)
  const threat = useThreatLevel()
  const nextUpgrade = selectedBuilding && canManageSelectedBuilding ? getNextUpgrade(selectedBuilding) : null
  const selectedBuildingHasModel = selectedBuilding ? canResolveBuildingModelAsset(selectedBuilding) : false
  const selectedBuildingMaxHealth = selectedBuilding ? maxHealthForBuilding(selectedBuilding) : 100
  const rushCost = selectedBuilding?.status === 'construction' && selectedBuilding.completesAt ? rushCompletionCrystalCost(selectedBuilding.completesAt - constructionNow) : 0
  const crystals = inventoryAmount(inventoryQuery.data?.inventory.items, 'aeolian-crystal')
  const selectedWorldTile = activeTile ? worldTiles.find((tile) => tile.x === activeTile.x && tile.y === activeTile.y) ?? null : null
  const terrainLabel = selectedWorldTile ? terrainLabels[selectedWorldTile.terrain] : activeTile ? getTerrainLabel(activeTile.x, activeTile.y) : 'Не выбран'
  const selectedResourceNode = activeTile ? resourceNodes.find((node) => node.tile.x === activeTile.x && node.tile.y === activeTile.y) ?? null : null
  const selectedFieldSpec = selectedBuilding ? fieldCropSpec(selectedBuilding.kind) : null
  const selectedFieldMaxStage = selectedFieldSpec && selectedBuilding?.isSuperCrop ? selectedFieldSpec.superStages : selectedFieldSpec?.stages ?? 0
  const selectedFieldStageReady = selectedFieldSpec && selectedBuilding?.fieldStageReadyAt ? selectedBuilding.fieldStageReadyAt <= constructionNow : Boolean(selectedBuilding?.fieldStageReady)
  const selectedFieldStage = selectedBuilding?.fieldStage ?? selectedBuilding?.growthStage ?? selectedBuilding?.cropStage ?? 0
  const selectedFieldReadyToHarvest = Boolean(selectedFieldSpec && selectedFieldMaxStage > 0 && selectedFieldStage >= selectedFieldMaxStage && selectedFieldStageReady)
  const selectedFieldReadyToAdvance = Boolean(selectedFieldSpec && selectedFieldStage > 0 && selectedFieldStage < selectedFieldMaxStage && selectedFieldStageReady)
  const selectedFieldNextAt = selectedFieldSpec ? selectedBuilding?.fieldStageReadyAt : null
  const upgradeMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'upgrade'),
    onSuccess: (result) => {
      if (result.building) {
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setUpgradeOpen(false)
      setUpgradeError('')
    },
    onError: (error) => {
      setUpgradeError(error instanceof Error ? error.message : 'Не удалось улучшить постройку')
    },
  })
  const advanceFieldMutation = useMutation({
    mutationFn: (buildingId: string) => advanceField(buildingId),
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const harvestFieldMutation = useMutation({
    mutationFn: (buildingId: string) => harvestField(buildingId),
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const rushMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'rush_complete'),
    onSuccess: (result) => {
      if (result.building) {
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setConstructionError('')
    },
    onError: (error) => {
      setConstructionError(formatActionError(error))
    },
  })
  const attackMonsterMutation = useMutation({
    mutationFn: (monsterId: string) => attackMonster(monsterId),
    onSuccess: (result) => {
      upsertMonster(toMonster(result.monster))
      void queryClient.invalidateQueries({ queryKey: ['monsters'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })

  useEffect(() => {
    if (selectedBuildingId) {
      setActiveTab('object')
    }
    setModelPreviewOpen(false)
  }, [selectedBuildingId])

  return (
    <aside className="inspector" aria-label="Инспектор">
      <h2>{selectedMonster ? monsterName(selectedMonster.type) : selectedBuilding ? selectedBuilding.name : activeTile ? `Тайл ${activeTile.x}:${activeTile.y}` : 'Карта мира'}</h2>
      <Tabs items={tabs} active={activeTab} onChange={setActiveTab}>
        {activeTab === 'tile' ? (
          <>
            <dl>
              <dt>Выбранный тайл</dt>
              <dd>{selectedTile ? `${selectedTile.x}, ${selectedTile.y}` : 'Нет'}</dd>
              <dt>Наведение</dt>
              <dd>{hoveredTile ? `${hoveredTile.x}, ${hoveredTile.y}` : 'Нет'}</dd>
              <dt>Чанк</dt>
              <dd>{chunk ? `${chunk.x}, ${chunk.y}` : 'Нет'}</dd>
              <dt>Поверхность</dt>
              <dd>{terrainLabel}</dd>
              <dt>Статус</dt>
              <dd>{activeTile ? 'Можно осмотреть, занять или проложить маршрут' : 'Выберите клетку на карте'}</dd>
              {selectedWorldTile?.terrain === 'forest' ? (
                <>
                  <dt>Густота леса</dt>
                  <dd>{selectedWorldTile.forest_density}/3</dd>
                </>
              ) : null}
              {selectedResourceNode ? (
                <>
                  <dt>Ресурсный узел</dt>
                  <dd>{resourceLabel(selectedResourceNode.resource)} · {selectedResourceNode.amount}/{selectedResourceNode.maxAmount}</dd>
                  <dt>Состояние узла</dt>
                  <dd>{resourceStateLabel[selectedResourceNode.state]}</dd>
                </>
              ) : null}
              {threat ? (
                <>
                  <dt>Угроза</dt>
                  <dd>уровень {threat.level}</dd>
                </>
              ) : null}
            </dl>
            <SegmentedControl items={claimModes} value={tool === 'raid' ? 'raid' : 'build'} label="Режим действия" onChange={setTool} />
          </>
        ) : null}
        {activeTab === 'object' ? (
          selectedMonster ? (
            <div className="inspector-card inspector-card-threat">
              <strong>{monsterName(selectedMonster.type)}</strong>
              <span>Состояние: {monsterStateLabel[selectedMonster.state]}</span>
              <span>Здоровье {selectedMonster.health}/{selectedMonster.maxHealth}</span>
              <span>Урон: {selectedMonster.damage}</span>
              <span>Агро-радиус: {selectedMonster.aggroRadius}</span>
              {selectedMonster.targetId ? <span>Цель: {selectedMonster.targetType} {selectedMonster.targetId}</span> : null}
              <meter min={0} max={selectedMonster.maxHealth} value={selectedMonster.health} />
            </div>
          ) : selectedBuilding ? (
            <div className="inspector-card">
              <strong>
                {selectedBuilding.name}, уровень {selectedBuilding.level}
              </strong>
              <span>Здоровье {selectedBuilding.health}/{selectedBuildingMaxHealth}</span>
              <span>Владелец: {selectedBuilding.owner}</span>
              {!canManageSelectedBuilding ? <span>Чужая постройка: управление недоступно</span> : null}
              <span>Состояние: {selectedBuilding.status === 'active' ? 'работает' : 'строится'}</span>
              {selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>До завершения: {formatRemaining(selectedBuilding.completesAt - constructionNow)}</span> : null}
              {selectedFieldSpec && selectedBuilding.status === 'active' && selectedFieldStage > 0 ? (
                <>
                  <span>Фаза роста: {selectedFieldStage}/{selectedFieldMaxStage}{selectedBuilding.isSuperCrop ? ' · супер-цикл' : ''}</span>
                  {selectedFieldReadyToHarvest ? <span>Урожай готов к сбору</span> : null}
                  {selectedFieldReadyToAdvance ? <span>Фаза завершена, нужна команда на рост</span> : null}
                  {!selectedFieldStageReady && selectedFieldNextAt ? <span>До конца фазы: {formatRemaining(selectedFieldNextAt - constructionNow)}</span> : null}
                </>
              ) : null}
              {selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>Мгновенно: {rushCost} крист.</span> : null}
              {selectedBuilding.status === 'construction' && rushCost > 0 && crystals < rushCost ? <small className="upgrade-error">Не хватает эолийских кристаллов: {crystals}/{rushCost}</small> : null}
              <span>Улучшение выполняется из меню этой постройки.</span>
              <meter min={0} max={selectedBuildingMaxHealth} value={selectedBuilding.health} />
              {modelPreviewOpen ? <BuildingModelPreview building={selectedBuilding} className="inspector-model-preview" /> : null}
              {constructionError ? <small className="upgrade-error" role="alert">{constructionError}</small> : null}
            </div>
          ) : (
            <div className="inspector-card">
              <strong>Постройка не выбрана</strong>
              <span>Нажмите на объект на карте, чтобы открыть меню здания.</span>
            </div>
          )
        ) : null}
        {activeTab === 'player' ? (
          <div className="inspector-card">
            <strong>Игрок: Северный двор</strong>
            <span>Союз: Караван Эолии</span>
            <span>Последняя активность: сейчас</span>
          </div>
        ) : null}
      </Tabs>
      <div className="inspector-actions">
        {selectedBuilding ? (
          <>
            {canManageSelectedBuilding ? <IconButton label="Улучшить" icon={TrendingUp} disabled={selectedBuilding.status !== 'active' || !nextUpgrade} onClick={() => setUpgradeOpen(true)} /> : null}
            {canManageSelectedBuilding && selectedBuilding.status === 'construction' ? (
              <IconButton
                label={`Завершить за ${rushCost} крист.`}
                icon={Gem}
                disabled={rushMutation.isPending || rushCost <= 0}
                onClick={() => {
                  setConstructionError('')
                  rushMutation.mutate(selectedBuilding.id)
                }}
              />
            ) : null}
            {canManageSelectedBuilding && selectedFieldSpec && selectedFieldStage < selectedFieldMaxStage ? (
              <IconButton
                label={selectedFieldStage <= 0 ? 'Запустить' : 'Следующая фаза'}
                icon={Sprout}
                disabled={selectedBuilding.status !== 'active' || (selectedFieldStage > 0 && !selectedFieldReadyToAdvance) || advanceFieldMutation.isPending}
                onClick={() => advanceFieldMutation.mutate(selectedBuilding.id)}
              />
            ) : null}
            {canManageSelectedBuilding && selectedFieldSpec ? (
              <IconButton
                label="Собрать урожай"
                icon={Sprout}
                disabled={selectedBuilding.status !== 'active' || !selectedFieldReadyToHarvest || harvestFieldMutation.isPending}
                onClick={() => harvestFieldMutation.mutate(selectedBuilding.id)}
              />
            ) : null}
            {canManageSelectedBuilding ? (
              <IconButton
                label="Удалить"
                icon={Trash2}
                onClick={() => {
                  deleteBuilding(selectedBuilding.id)
                  void deleteBuildingRequest(selectedBuilding.id).catch(() => undefined)
                }}
              />
            ) : null}
            {selectedBuildingHasModel ? (
              <IconButton
                label={modelPreviewOpen ? 'Скрыть 3D' : '3D preview'}
                icon={Box}
                active={modelPreviewOpen}
                onClick={() => setModelPreviewOpen((current) => !current)}
              />
            ) : null}
          </>
        ) : null}
        <IconButton label="Построить" icon={Hammer} active={tool === 'build'} disabled={!activeTile} onClick={() => setBuildMenuOpen(true)} />
        {selectedMonster ? (
          <IconButton label="Атаковать" icon={Swords} active disabled={attackMonsterMutation.isPending} onClick={() => attackMonsterMutation.mutate(selectedMonster.id)} />
        ) : null}
        <IconButton label="Маршрут" icon={Route} active={tool === 'road'} disabled={!activeTile} onClick={() => setTool('road')} />
        <IconButton label="Рейд" icon={Swords} active={tool === 'raid'} disabled={!activeTile} onClick={() => setTool('raid')} />
      </div>
      <UpgradeModal
        building={selectedBuilding}
        nextUpgrade={nextUpgrade}
        open={upgradeOpen}
        pending={upgradeMutation.isPending}
        error={upgradeError}
        onClose={() => {
          setUpgradeOpen(false)
          setUpgradeError('')
        }}
        onUpgrade={() => {
          if (selectedBuilding) {
            setUpgradeError('')
            upgradeMutation.mutate(selectedBuilding.id)
          }
        }}
      />
    </aside>
  )
}

function UpgradeModal({
  building,
  nextUpgrade,
  open,
  pending,
  error,
  onClose,
  onUpgrade,
}: {
  building: PlacedBuilding | null
  nextUpgrade: UpgradeInfo | null
  open: boolean
  pending: boolean
  error: string
  onClose: () => void
  onUpgrade: () => void
}) {
  if (!building || !nextUpgrade) {
    return null
  }
  const previewAsset = upgradePreviewAsset(building, nextUpgrade)
  return (
    <Modal title="Улучшение постройки" open={open} onClose={onClose}>
      <div className="upgrade-dialog">
        <div className="upgrade-summary">
          <div className={`upgrade-preview build-icon-${nextUpgrade.type}`}>
            {previewAsset ? (
              <img src={previewAsset} alt={`Модель: ${nextUpgrade.name}, уровень ${nextUpgrade.level}`} draggable={false} />
            ) : (
              <TrendingUp size={34} aria-hidden="true" />
            )}
          </div>
          <strong>{building.name}</strong>
          <span>
            Уровень {building.level} {'->'} {nextUpgrade.level}
          </span>
          <span>{nextUpgrade.type === building.kind ? 'Улучшение текущей модели' : `Переход в: ${nextUpgrade.name}`}</span>
        </div>
        <dl className="upgrade-stats">
          {upgradeComparisons(building, nextUpgrade).map((item) => (
            <div key={item.label}>
              <dt>{item.label}</dt>
              <dd>
                <span>{item.before}</span>
                <strong>{item.after}</strong>
              </dd>
            </div>
          ))}
        </dl>
        <div className="upgrade-cost">
          <span>Стоимость</span>
          {nextUpgrade.cost.length > 0 ? (
            nextUpgrade.cost.map((cost) => (
              <em key={`${cost.resource}:${cost.amount}`} title={`${resourceLabel(cost.resource)}: ${cost.amount}`}>
                <ResourceIcon id={cost.resource} label={resourceLabel(cost.resource)} />
                {cost.amount}
              </em>
            ))
          ) : (
            <em>бесплатно</em>
          )}
        </div>
        <div className="upgrade-actions">
          <button className="text-button" type="button" onClick={onClose}>
            Отмена
          </button>
          <button className="text-button text-button-primary" type="button" disabled={pending} onClick={onUpgrade}>
            Улучшить
          </button>
        </div>
        {error ? <p className="upgrade-error" role="alert">{error}</p> : null}
      </div>
    </Modal>
  )
}

function upgradePreviewAsset(building: PlacedBuilding, nextUpgrade: UpgradeInfo) {
  return buildingSpriteAsset({
    ...building,
    id: `${building.id}:upgrade-preview`,
    kind: nextUpgrade.type,
    name: nextUpgrade.name,
    level: nextUpgrade.level,
    status: 'active',
    state: 'active',
    health: nextUpgrade.health,
    maxHealth: nextUpgrade.health,
    completesAt: null,
  })
}

function formatRemaining(ms: number) {
	const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
	const minutes = Math.floor(totalSeconds / 60)
	const seconds = totalSeconds % 60
	return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function rushCompletionCrystalCost(ms: number) {
	if (ms <= 0) {
		return 0
	}
	const step = 3 * 60 * 1000
	if (ms < step) {
		return 1
	}
	return 2 + Math.floor((ms - step) / step)
}

function formatActionError(error: unknown) {
	if (error instanceof ApiClientError) {
		const fields = error.apiError.fields ?? {}
		const crystal = fields['aeolian-crystal']
		if (crystal) {
			return `Не хватает эолийских кристаллов: ${crystal}`
		}
		return error.message
	}
	return error instanceof Error ? error.message : 'Не удалось выполнить действие'
}

function getTerrainLabel(x: number, y: number) {
  const marker = Math.abs((x * 17 + y * 31) % 7)
  return ['луг', 'редколесье', 'каменистый склон', 'руины', 'нефтяная скважина', 'песчаная почва', 'дорога'][marker]
}

function resourceLabel(resource: string) {
  const labels: Record<string, string> = {
    wood: 'Древесина',
    stone: 'Камень',
    coins: 'Монеты',
    flax: 'Лен',
    seeds: 'Семена',
    windleaf: 'Ветролист',
    mushrooms: 'Грибы',
    herbs: 'Травы',
    reed: 'Тростник',
    dyes: 'Красители',
    oil_plants: 'Масличные растения',
    sugar_cane: 'Сахарный тростник',
    crystal_fruit: 'Кристальные плоды',
    planks: 'Доски',
    stone_block: 'Каменный блок',
    brick: 'Кирпич',
    glass: 'Стекло',
    premium_planks: 'Премиум-доски',
    rope: 'Веревка',
    iron_ingot: 'Железный слиток',
    gold_ingot: 'Золотой слиток',
    'super-mushrooms': 'Супер-грибы',
    'super-windleaf': 'Супер-ветролист',
    'super-seeds': 'Супер-семена',
    'super-fiber': 'Супер-волокно',
    emerald_dust: 'Изумрудная пыль',
    oil: 'Нефть',
  }
  return labels[resource] ?? resource
}

type UpgradeInfo = {
  type: BuildingKind
  name: string
  level: number
  buildSeconds: number
  population: number
  health: number
  footprint: { width: number; height: number }
  cost: { resource: string; amount: number }[]
}

type UpgradeComparison = {
  label: string
  before: string
  after: string
}

function getNextUpgrade(building: PlacedBuilding): UpgradeInfo | null {
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  if (!spec) {
    return null
  }
  const nextLevel = spec.upgradeLevels?.find((level) => level.level === building.level + 1)
  if (nextLevel) {
    return {
      type: spec.type as BuildingKind,
      name: spec.name,
      level: nextLevel.level,
      buildSeconds: nextLevel.buildSeconds,
      population: nextLevel.population,
      health: nextLevel.health,
      footprint: spec.footprint,
      cost: [...nextLevel.cost],
    }
  }
  const finalLevel = spec.upgradeLevels?.find((level) => level.level === building.level && level.nextType)
  const nextType = finalLevel?.nextType ?? spec.upgradeTo[0]
  const nextSpec = nextType ? buildingCatalog.find((item) => item.type === nextType) : null
  if (!nextSpec) {
    return null
  }
  return {
    type: nextSpec.type as BuildingKind,
    name: nextSpec.name,
    level: nextSpec.level,
    buildSeconds: nextSpec.buildSeconds,
    population: nextSpec.population,
    health: nextSpec.health ?? 100,
    footprint: nextSpec.footprint,
    cost: [...nextSpec.cost],
  }
}

function maxHealthForBuilding(building: PlacedBuilding) {
  if (building.maxHealth && building.maxHealth > 0) {
    return building.maxHealth
  }
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  const levelHealth = spec?.upgradeLevels?.find((level) => level.level === building.level)?.health
  return levelHealth ?? spec?.health ?? 100
}

function upgradeComparisons(building: PlacedBuilding, nextUpgrade: UpgradeInfo): UpgradeComparison[] {
  const current = getCurrentStats(building)
  const comparisons: UpgradeComparison[] = [
    { label: 'Прочность', before: String(current.health), after: String(nextUpgrade.health) },
    { label: 'Размер', before: `${current.footprint.width}x${current.footprint.height}`, after: `${nextUpgrade.footprint.width}x${nextUpgrade.footprint.height}` },
    { label: 'Время работ', before: 'сейчас', after: formatDuration(nextUpgrade.buildSeconds) },
  ]
  if (building.kind === 'town_hall') {
    comparisons.push({ label: 'Лимит построек', before: String(buildingLimitForLevel(building.level)), after: String(buildingLimitForLevel(nextUpgrade.level)) })
  } else if (current.population > 0 || nextUpgrade.population > 0) {
    comparisons.push({ label: 'Население', before: String(current.population), after: String(nextUpgrade.population) })
  }
  return comparisons
}

function getCurrentStats(building: PlacedBuilding) {
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  const level = spec?.upgradeLevels?.find((item) => item.level === building.level)
  return {
    health: level?.health ?? spec?.health ?? building.health,
    population: level?.population ?? spec?.population ?? 0,
    footprint: spec?.footprint ?? { width: 1, height: 1 },
  }
}

function buildingLimitForLevel(level: number) {
  return 8 + Math.max(0, level - 1) * 3
}

function formatDuration(seconds: number) {
  if (seconds <= 0) {
    return 'мгновенно'
  }
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  if (hours > 0) {
    return `${hours} ч ${minutes} мин`
  }
  if (minutes > 0) {
    return `${minutes} мин ${rest} сек`
  }
  return `${rest} сек`
}

const resourceStateLabel = {
  neutral: 'нейтральный',
  claimed: 'захвачен',
  depleted: 'истощен',
} as const

const terrainLabels = {
  grass: 'луг',
  forest: 'лес',
  water: 'река',
  mountain: 'горы',
  road: 'дорога',
  oil_well: 'нефтяная скважина',
  ruins: 'руины',
} as const

function monsterName(type: string) {
  const names: Record<string, string> = {
    roaming_melee: 'Бродячий налетчик',
    resource_guardian: 'Страж залежи',
    ruins_guardian: 'Сторож руин',
    forest_stalker: 'Лесной следопыт',
    spore_beast: 'Споровый зверь',
    ironback_brute: 'Железоспин',
    ember_wisp: 'Тлеющий огонек',
    ancient_colossus: 'Древний колосс',
  }
  return names[type] ?? type
}

const monsterStateLabel: Record<string, string> = {
  idle: 'выжидает',
  wandering: 'бродит',
  aggro: 'преследует',
  attacking: 'атакует',
  dead: 'повержен',
}
