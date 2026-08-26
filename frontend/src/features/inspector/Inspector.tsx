import { useEffect, useState } from 'react'
import { Hammer, Route, Sprout, Swords, Trash2, TreePine, TrendingUp } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { tileToChunk } from '../../game/coordinates/iso'
import { useGameStore, type BuildingKind, type PlacedBuilding } from '../../game/state/useGameStore'
import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { deleteBuilding as deleteBuildingRequest, patchBuilding, toPlacedBuilding } from '../../shared/api/buildings'
import { harvestWindleafField } from '../../shared/api/economy'
import { chopForest } from '../../shared/api/world'
import { IconButton, Modal, SegmentedControl, Tabs } from '../../shared/ui'
import { ResourceIcon } from '../resources/ResourceIcon'

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
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const tool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const updateWorldTile = useGameStore((state) => state.updateWorldTile)
  const queryClient = useQueryClient()
  const activeTile = selectedTile ?? hoveredTile
  const chunk = activeTile ? tileToChunk(activeTile) : null
  const selectedBuilding = buildings.find((building) => building.id === selectedBuildingId) ?? null
  const nextUpgrade = selectedBuilding ? getNextUpgrade(selectedBuilding) : null
  const selectedWorldTile = activeTile ? worldTiles.find((tile) => tile.x === activeTile.x && tile.y === activeTile.y) ?? null : null
  const terrainLabel = selectedWorldTile ? terrainLabels[selectedWorldTile.terrain] : activeTile ? getTerrainLabel(activeTile.x, activeTile.y) : 'Не выбран'
  const selectedResourceNode = activeTile ? resourceNodes.find((node) => node.tile.x === activeTile.x && node.tile.y === activeTile.y) ?? null : null
  const chopMutation = useMutation({
    mutationFn: chopForest,
    onSuccess: (result) => {
      updateWorldTile(result.tile)
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      void queryClient.invalidateQueries({ queryKey: ['world'] })
    },
  })
  const upgradeMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'upgrade'),
    onSuccess: (result) => {
      if (result.building) {
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setUpgradeOpen(false)
    },
  })
  const harvestFieldMutation = useMutation({
    mutationFn: () => harvestWindleafField(false),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })

  useEffect(() => {
    if (selectedBuildingId) {
      setActiveTab('object')
    }
  }, [selectedBuildingId])

  return (
    <aside className="inspector" aria-label="Инспектор">
      <h2>{selectedBuilding ? selectedBuilding.name : activeTile ? `Тайл ${activeTile.x}:${activeTile.y}` : 'Карта мира'}</h2>
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
            </dl>
            <SegmentedControl items={claimModes} value={tool === 'raid' ? 'raid' : 'build'} label="Режим действия" onChange={setTool} />
          </>
        ) : null}
        {activeTab === 'object' ? (
          selectedBuilding ? (
            <div className="inspector-card">
              <strong>
                {selectedBuilding.name}, уровень {selectedBuilding.level}
              </strong>
              <span>Здоровье {selectedBuilding.health}/100</span>
              <span>Владелец: {selectedBuilding.owner}</span>
              <span>Состояние: {selectedBuilding.status === 'active' ? 'работает' : 'строится'}</span>
              {selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>До завершения: {formatRemaining(selectedBuilding.completesAt - constructionNow)}</span> : null}
              <span>Улучшение выполняется из меню этой постройки.</span>
              <meter min={0} max={100} value={selectedBuilding.health} />
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
            <IconButton label="Улучшить" icon={TrendingUp} disabled={selectedBuilding.status !== 'active' || !nextUpgrade} onClick={() => setUpgradeOpen(true)} />
            {selectedBuilding.kind === 'field_bed' ? <IconButton label="Собрать урожай" icon={Sprout} disabled={selectedBuilding.status !== 'active' || harvestFieldMutation.isPending} onClick={() => harvestFieldMutation.mutate()} /> : null}
            <IconButton
              label="Удалить"
              icon={Trash2}
              onClick={() => {
                deleteBuilding(selectedBuilding.id)
                void deleteBuildingRequest(selectedBuilding.id).catch(() => undefined)
              }}
            />
          </>
        ) : null}
        <IconButton label="Построить" icon={Hammer} active={tool === 'build'} disabled={!activeTile} onClick={() => setTool('build')} />
        <IconButton
          label="Срубить лес"
          icon={TreePine}
          disabled={!selectedWorldTile || selectedWorldTile.terrain !== 'forest' || selectedWorldTile.forest_density <= 0 || chopMutation.isPending}
          onClick={() => {
            if (selectedWorldTile) {
              chopMutation.mutate({ x: selectedWorldTile.x, y: selectedWorldTile.y })
            }
          }}
        />
        <IconButton label="Маршрут" icon={Route} active={tool === 'road'} disabled={!activeTile} onClick={() => setTool('road')} />
        <IconButton label="Рейд" icon={Swords} active={tool === 'raid'} disabled={!activeTile} onClick={() => setTool('raid')} />
      </div>
      <UpgradeModal
        building={selectedBuilding}
        nextUpgrade={nextUpgrade}
        open={upgradeOpen}
        pending={upgradeMutation.isPending}
        onClose={() => setUpgradeOpen(false)}
        onUpgrade={() => {
          if (selectedBuilding) {
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
  onClose,
  onUpgrade,
}: {
  building: PlacedBuilding | null
  nextUpgrade: UpgradeInfo | null
  open: boolean
  pending: boolean
  onClose: () => void
  onUpgrade: () => void
}) {
  if (!building || !nextUpgrade) {
    return null
  }
  return (
    <Modal title="Улучшение постройки" open={open} onClose={onClose}>
      <div className="upgrade-dialog">
        <div className="upgrade-summary">
          <strong>{building.name}</strong>
          <span>
            Уровень {building.level} {'->'} {nextUpgrade.level}
          </span>
          <span>{nextUpgrade.type === building.kind ? 'Улучшение текущей модели' : `Переход в: ${nextUpgrade.name}`}</span>
        </div>
        <dl className="upgrade-stats">
          <div>
            <dt>Население</dt>
            <dd>{nextUpgrade.population}</dd>
          </div>
          <div>
            <dt>Прочность</dt>
            <dd>{nextUpgrade.health}</dd>
          </div>
          <div>
            <dt>Время</dt>
            <dd>{formatDuration(nextUpgrade.buildSeconds)}</dd>
          </div>
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
      </div>
    </Modal>
  )
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function getTerrainLabel(x: number, y: number) {
  const marker = Math.abs((x * 17 + y * 31) % 7)
  return ['луг', 'редколесье', 'каменистый склон', 'руины', 'нефтяная скважина', 'песчаная почва', 'дорога'][marker]
}

function resourceLabel(resource: string) {
  const labels: Record<string, string> = {
    wood: 'Древесина',
    stone: 'Камень',
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
  cost: { resource: string; amount: number }[]
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
    cost: [...nextSpec.cost],
  }
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
