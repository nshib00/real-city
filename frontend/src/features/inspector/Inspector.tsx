import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Box, Gem, Hammer, Move, RotateCw, Route, Shield, Sprout, Star, Swords, Trash2, TrendingUp } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { playUiSound } from '../../audio/playUiSound'
import { playCombatSound } from '../../audio/voiceManager'
import { cellLabel, districtFromTile, districtLabel } from '../../game/coordinates/district'
import { HealthBar } from '../../game/HealthBar'
import { maxHealthForBuilding } from '../../game/health'
import { BuildingModelPreview } from '../../game/renderers/BuildingModelPreview'
import { canResolveBuildingModelAsset } from '../../game/renderers/buildingRegistry'
import { buildingSpriteAsset } from '../../game/renderers/buildingSpriteAssets'
import { useGameStore, type BuildingKind, type PlacedBuilding } from '../../game/state/useGameStore'
import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import { deleteBuilding as deleteBuildingRequest, patchBuilding, placeBuilding, relocateBuilding, toPlacedBuilding, type BuildingResponse } from '../../shared/api/buildings'
import { ruinRestoration } from './ruinRestoration'
import { playBuildingSound } from '../buildings/buildingAudio'
import { ApiClientError } from '../../shared/api/client'
import { advanceField, harvestField, listProductionJobs, patchResourceNode, type InventoryResponse } from '../../shared/api/economy'
import { listPendingWeaponAttacks, useWeaponOnMonster, toMonster, type MonsterLootResponse, type MonsterResponse, type PendingWeaponAttack } from '../../shared/api/monsters'
import { weaponFuseLabel } from './weaponFuse'
import { IconButton, Modal, SegmentedControl, Tabs } from '../../shared/ui'
import { formatRemaining } from '../../shared/time/formatRemaining'
import { useAuthStore } from '../auth/useAuthStore'
import { getPublicPlayer } from '../auth/api'
import { inventoryAmount, useInventory } from '../economy/useInventory'
import { fieldHarvestSound, playConfirmedCoinChange, playConfirmedRareReward, resourceGatherSound } from '../economy/economyAudio'
import { fieldCropSpec } from '../fields/fieldGrowth'
import { ResourceIcon } from '../resources/ResourceIcon'
import { useThreatLevel } from '../threat/ThreatPanel'
import { showToast } from '../notifications/toast'

type InspectorTab = 'tile' | 'object' | 'player'

const tabs = [
  { id: 'tile', label: 'Клетка' },
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
  const [cannonError, setCannonError] = useState('')
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [selectedWeapon, setSelectedWeapon] = useState('throwing_knives')
  const [weaponMenuOpen, setWeaponMenuOpen] = useState(false)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const relocatingBuildingId = useGameStore((state) => state.relocatingBuildingId)
  const setRelocatingBuildingId = useGameStore((state) => state.setRelocatingBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const tool = useGameStore((state) => state.tool)
  const setTool = useGameStore((state) => state.setTool)
  const setBuildMenuOpen = useGameStore((state) => state.setBuildMenuOpen)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const upsertResourceNode = useGameStore((state) => state.upsertResourceNode)
  const upsertMonster = useGameStore((state) => state.upsertMonster)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const queryClient = useQueryClient()
  const inventoryQuery = useInventory()
  const player = useAuthStore((state) => state.player)
  const pendingWeaponsQuery = useQuery({
    queryKey: ['combat', 'attacks'],
    queryFn: listPendingWeaponAttacks,
    enabled: Boolean(player),
    refetchInterval: 5000,
  })
  const oilJobsQuery = useQuery({ queryKey: ['production', 'jobs'], queryFn: listProductionJobs, enabled: Boolean(player), refetchInterval: 5000 })
  const activeTile = selectedTile ?? hoveredTile
  const selectedBuilding = buildings.find((building) => building.id === selectedBuildingId) ?? null
  const canManageSelectedBuilding = Boolean(selectedBuilding && player && selectedBuilding.owner === player.id)
  const ownerQuery = useQuery({
    queryKey: ['players', 'public', selectedBuilding?.owner],
    queryFn: () => getPublicPlayer(selectedBuilding!.owner),
    enabled: Boolean(selectedBuilding?.owner && selectedBuilding.owner !== player?.id),
    staleTime: 60_000,
    retry: false,
  })
  const ownerName = canManageSelectedBuilding ? player?.profile.display_name || player?.name : ownerQuery.data?.display_name
  const ownerLevel = canManageSelectedBuilding ? player?.profile.level : ownerQuery.data?.level
  const selectedMonster = useGameStore((state) => state.monsters.find((monster) => monster.id === selectedMonsterId) ?? null)
  const threat = useThreatLevel()
  const nextUpgrades = selectedBuilding && canManageSelectedBuilding ? getNextUpgrades(selectedBuilding) : []
  const selectedBuildingHasModel = selectedBuilding ? canResolveBuildingModelAsset(selectedBuilding) : false
  const selectedBuildingMaxHealth = selectedBuilding ? maxHealthForBuilding(selectedBuilding) : 100
  const rushCost = selectedBuilding?.status === 'construction' && selectedBuilding.completesAt ? rushCompletionCrystalCost(selectedBuilding.completesAt - constructionNow) : 0
  const crystals = inventoryAmount(inventoryQuery.data?.inventory.items, 'aeolian-crystal')
  const cannonCharges = selectedBuilding?.cannonAmmo ? inventoryAmount(inventoryQuery.data?.inventory.items, selectedBuilding.cannonAmmo) : 0
  const cannonIdleReason = selectedBuilding && ['defense_cannon', 'defense_bolt_thrower', 'defense_storm_coil'].includes(selectedBuilding.kind) && selectedBuilding.cannonEnabled
    ? selectedBuilding.state === 'ruined' || selectedBuilding.status === 'construction' ? 'Стройка или разрушение'
      : selectedBuilding.health * 4 < selectedBuildingMaxHealth ? 'Повреждена: HP ниже 25%'
        : selectedBuilding.cannonAmmo && cannonCharges < 1 ? 'Нет зарядов' : null
    : null
  const selectedWorldTile = activeTile ? worldTiles.find((tile) => tile.x === activeTile.x && tile.y === activeTile.y) ?? null : null
  const selectedRuin = selectedWorldTile?.terrain === 'ruins' && selectedWorldTile.ruin_type ? ruinRestoration[selectedWorldTile.ruin_type] : null
  const ruinOccupied = selectedWorldTile ? buildings.some((item) => item.state !== 'ruined' && item.tile.x === selectedWorldTile.x && item.tile.y === selectedWorldTile.y) : false
  const terrainLabel = selectedWorldTile
    ? selectedWorldTile.terrain === 'ruins' ? ruinTypeLabels[selectedWorldTile.ruin_type ?? ''] ?? 'руины' : terrainLabels[selectedWorldTile.terrain] ?? 'луг'
    : activeTile ? 'Загрузка...' : 'Не выбран'
  const selectedResourceNode = activeTile ? resourceNodes.find((node) => node.tile.x === activeTile.x && node.tile.y === activeTile.y && (node.resource !== 'oil' || node.state !== 'depleted')) ?? null : null
  const selectedOilNode = selectedBuilding?.kind === 'oil_well' ? resourceNodes.find((node) => node.resource === 'oil' && node.tile.x === selectedBuilding.tile.x && node.tile.y === selectedBuilding.tile.y) : null
  const selectedOilJob = selectedBuilding?.kind === 'oil_well' ? oilJobsQuery.data?.jobs.find((job) => job.building_id === selectedBuilding.id && (job.state === 'running' || job.state === 'ready')) : null
  const selectedFieldSpec = selectedBuilding ? fieldCropSpec(selectedBuilding.kind) : null
  const selectedFieldMaxStage = selectedFieldSpec && selectedBuilding?.isSuperCrop ? selectedFieldSpec.superStages : selectedFieldSpec?.stages ?? 0
  const selectedFieldStageReady = selectedFieldSpec && selectedBuilding?.fieldStageReadyAt ? selectedBuilding.fieldStageReadyAt <= constructionNow : Boolean(selectedBuilding?.fieldStageReady)
  const selectedFieldStage = selectedBuilding?.fieldStage ?? selectedBuilding?.growthStage ?? selectedBuilding?.cropStage ?? 0
  const selectedFieldReadyToHarvest = Boolean(selectedFieldSpec && selectedFieldMaxStage > 0 && selectedFieldStage >= selectedFieldMaxStage && selectedFieldStageReady)
  const selectedFieldReadyToAdvance = Boolean(selectedFieldSpec && selectedFieldStage > 0 && selectedFieldStage < selectedFieldMaxStage && selectedFieldStageReady)
  const selectedFieldNextAt = selectedFieldSpec ? selectedBuilding?.fieldStageReadyAt : null
  const upgradeMutation = useMutation({
    mutationFn: ({ buildingId, targetType }: { buildingId: string; targetType?: BuildingKind }) => patchBuilding(buildingId, 'upgrade', targetType),
    onSuccess: (result) => {
      if (result.building) playBuildingSound(result.building.state === 'active' ? 'build.upgrade.completed' : 'build.upgrade.started', result.building.id, result.building.state === 'active' ? 'completion' : 'upgrade_started')
      if (result.building) {
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setUpgradeOpen(false)
      setUpgradeError('')
    },
    onError: (error) => {
      playUiSound(error instanceof ApiClientError && error.apiError.fields?.coins ? 'economy.coin.insufficient' : 'ui.action.invalid')
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
      playUiSound(fieldHarvestSound(result.building.type))
      playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const resourceMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'claim' | 'harvest' }) => patchResourceNode(id, action),
    onSuccess: (result, variables) => {
      const node = result.node
      upsertResourceNode({ id: node.id, type: node.type, resource: node.resource, amount: node.amount,
        maxAmount: node.max_amount, state: node.state, ownerId: node.owner_id,
        tile: { x: node.tile_x, y: node.tile_y }, respawnAt: node.respawn_at ? Date.parse(node.respawn_at) : null })
      playUiSound(variables.action === 'claim' ? 'economy.node.claimed' : resourceGatherSound(node.resource))
      playConfirmedRareReward(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      if (variables.action === 'harvest' && node.state === 'depleted') playUiSound('economy.node.depleted')
      playConfirmedCoinChange(queryClient.getQueryData<{ inventory: InventoryResponse }>(['economy', 'inventory'])?.inventory, result.inventory)
      void queryClient.invalidateQueries({ queryKey: ['resources', 'nodes'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: () => playUiSound('ui.action.invalid'),
  })
  const rushMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'rush_complete'),
    onSuccess: (result) => {
      if (result.building) playBuildingSound('build.rushed', result.building.id, 'rushed')
      if (result.building) {
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setConstructionError('')
    },
    onError: (error) => {
      playUiSound('ui.action.invalid')
      setConstructionError(formatActionError(error))
    },
  })
  const repairMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'repair'),
    onSuccess: (result) => {
      if (result.building) {
        playBuildingSound('build.repaired', result.building.id, 'repaired')
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
    },
    onError: (error) => { playUiSound('ui.action.invalid'); showToast('warning', formatActionError(error)) },
  })
  const rotateMutation = useMutation({
    mutationFn: (item: PlacedBuilding) => relocateBuilding(item.id, item.tile, ((item.rotation ?? 0) + 1) % 4),
    onSuccess: (result) => {
      addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
    },
    onError: (error) => { playUiSound('ui.action.invalid'); showToast('warning', formatActionError(error)) },
  })
  const cancelConstructionMutation = useMutation({
    mutationFn: (buildingId: string) => patchBuilding(buildingId, 'cancel'),
    onSuccess: (_result, buildingId) => {
      playBuildingSound('build.cancelled', buildingId, 'cancelled')
      deleteBuilding(buildingId)
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: () => playUiSound('ui.action.invalid'),
  })
  const cannonMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) => patchBuilding(id, enabled ? 'enable_cannon' : 'disable_cannon'),
    onSuccess: (result) => {
      if (result.building) addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setCannonError('')
    },
    onError: (error) => { playUiSound('ui.action.invalid'); setCannonError(formatActionError(error)) },
  })
  const trapMutation = useMutation({
    mutationFn: (id: string) => patchBuilding(id, 'reload_trap'),
    onSuccess: (result) => {
      if (result.building) addBuilding(toPlacedBuilding(result.building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      setCannonError('')
    },
    onError: (error) => { playUiSound('ui.action.invalid'); setCannonError(formatActionError(error)) },
  })
  const deleteMutation = useMutation({
    mutationFn: deleteBuildingRequest,
    onSuccess: (_result, buildingId) => {
      playBuildingSound('build.demolished', buildingId, 'demolished')
      queryClient.setQueriesData<{ buildings: BuildingResponse[] }>({ queryKey: ['buildings'] }, (current) => current
        ? { ...current, buildings: current.buildings.filter((building) => building.id !== buildingId) }
        : current)
      deleteBuilding(buildingId)
      setDeleteOpen(false)
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['production', 'jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })
  const ruinMutation = useMutation({
    mutationFn: () => placeBuilding({ type: selectedWorldTile!.ruin_type as BuildingKind, tile_x: selectedWorldTile!.x, tile_y: selectedWorldTile!.y }),
    onSuccess: ({ building }) => {
      addBuilding(toPlacedBuilding(building))
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      showToast('info', 'Восстановление руины началось')
    },
    onError: (error) => showToast('error', error instanceof Error ? error.message : 'Не удалось захватить руину'),
  })
  const availableWeapons = resourceCatalog.filter((resource) => resource.category === 'weapons' && inventoryAmount(inventoryQuery.data?.inventory.items, resource.id) > 0)
  const weaponCatalog = resourceCatalog.filter((resource) => resource.category === 'weapons')
  const selectedMonsterAttacks = pendingWeaponsQuery.data?.attacks.filter((attack) => attack.monster_id === selectedMonsterId) ?? []
  const attackMonsterMutation = useMutation({
    mutationFn: ({ monsterId, weaponId }: { monsterId: string; weaponId: string }) => useWeaponOnMonster(monsterId, weaponId),
    onSuccess: (result, variables) => {
      setWeaponMenuOpen(false)
      if (result.monster) {
        playCombatSound('combat.player.attack')
        playCombatSound('combat.player.hit')
        const monster = result.monster
        queryClient.setQueriesData<{ monsters: MonsterResponse[] }>({ queryKey: ['monsters'] }, (current) => current
          ? { ...current, monsters: monster.state === 'dead'
            ? current.monsters.filter((item) => item.id !== monster.id)
            : current.monsters.map((item) => item.id === monster.id ? monster : item) }
          : current)
        upsertMonster(toMonster(monster))
      } else {
        queryClient.setQueryData<{ attacks: PendingWeaponAttack[] }>(['combat', 'attacks'], (current) => ({
          attacks: [...(current?.attacks ?? []), { ...result.attack, monster_id: variables.monsterId }],
        }))
        showToast('info', 'Заряд установлен. Время срабатывания показано в карточке монстра.')
      }
      void queryClient.invalidateQueries({ queryKey: ['monsters'] })
      if (result.loot) {
        const drop = result.loot
        queryClient.setQueriesData<{ loot: MonsterLootResponse[] }>({ queryKey: ['monster-loot'] }, (current) => current
          ? { loot: current.loot.some((item) => item.id === drop.id) ? current.loot : [...current.loot, drop] }
          : current)
      }
      if (result.monster?.state === 'dead' && !result.loot) void queryClient.invalidateQueries({ queryKey: ['monster-loot'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      void queryClient.invalidateQueries({ queryKey: ['combat', 'attacks'] })
    },
    onError: (error) => {
      showToast('error', error instanceof Error ? error.message : 'Не удалось применить оружие')
      void queryClient.invalidateQueries({ queryKey: ['monsters'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
  })

  useEffect(() => {
    if (selectedBuildingId) {
      setActiveTab('object')
    }
    setModelPreviewOpen(false)
    setDeleteOpen(false)
    setCannonError('')
  }, [selectedBuildingId])

  useEffect(() => {
    setWeaponMenuOpen(false)
    if (selectedMonsterId) setActiveTab('object')
  }, [selectedMonsterId])

  return (
    <aside className={`inspector${selectedMonster ? ' inspector-monster' : ''}`} aria-label="Инспектор">
      <h2>{selectedMonster ? monsterName(selectedMonster.type) : selectedBuilding ? selectedBuilding.name : activeTile ? `Клетка ${cellLabel(activeTile)}` : 'Карта мира'}</h2>
      <Tabs items={tabs} active={activeTab} onChange={setActiveTab}>
        {activeTab === 'tile' ? (
          <>
            <dl>
              <dt>Выбранная клетка</dt>
              <dd>{selectedTile ? cellLabel(selectedTile) : 'Нет'}</dd>
              <dt>Наведение</dt>
              <dd>{hoveredTile ? cellLabel(hoveredTile) : 'Нет'}</dd>
              <dt>Район</dt>
              <dd>{activeTile ? districtLabel(districtFromTile(activeTile)) : 'Нет'}</dd>
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
              {selectedRuin ? (
                <>
                  <dt>Восстановление</dt>
                  <dd>{selectedRuin.hours} ч · {selectedRuin.coins.toLocaleString('ru-RU')} монет</dd>
                  <dt>Владение</dt>
                  <dd>{ruinOccupied ? 'Руина занята' : 'Свободна'}</dd>
                  {!ruinOccupied ? <dd><button type="button" disabled={ruinMutation.isPending} onClick={() => ruinMutation.mutate()}>Захватить и восстановить</button></dd> : null}
                </>
              ) : null}
              {selectedResourceNode ? (
                <>
                  <dt>Ресурсный узел</dt>
                  <dd>{resourceLabel(selectedResourceNode.resource)} · {selectedResourceNode.amount}/{selectedResourceNode.maxAmount}</dd>
                  <dt>Состояние узла</dt>
                  <dd>{resourceStateLabel[selectedResourceNode.state]}</dd>
                  {selectedResourceNode.resource === 'oil' && selectedResourceNode.state === 'neutral' ? <dd>Постройте нефтяную вышку, чтобы занять месторождение.</dd> : null}
                  {selectedResourceNode.resource !== 'oil' && selectedResourceNode.state === 'neutral' ? <dd><button type="button" disabled={resourceMutation.isPending} onClick={() => resourceMutation.mutate({ id: selectedResourceNode.id, action: 'claim' })}>Захватить узел</button></dd> : null}
                  {selectedResourceNode.resource !== 'oil' && selectedResourceNode.state === 'claimed' && selectedResourceNode.ownerId === player?.id && selectedResourceNode.amount > 0 ? <dd><button type="button" disabled={resourceMutation.isPending} onClick={() => resourceMutation.mutate({ id: selectedResourceNode.id, action: 'harvest' })}>Собрать ресурс</button></dd> : null}
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
              <IconButton label="Выбрать оружие" icon={Swords} active onClick={() => setWeaponMenuOpen(true)} />
              <span>Состояние: {monsterStateLabel[selectedMonster.state]}</span>
              <span>Здоровье {selectedMonster.health}/{selectedMonster.maxHealth}</span>
              <span>Урон: {selectedMonster.damage}</span>
              <span>Агро-радиус: {selectedMonster.aggroRadius}</span>
              {selectedMonster.targetId ? <span>Цель: {selectedMonster.targetType} {selectedMonster.targetId}</span> : null}
              <HealthBar health={selectedMonster.health} maxHealth={selectedMonster.maxHealth} />
              {selectedMonsterAttacks.map((attack) => (
                <span key={attack.id}>До срабатывания — {resourceCatalog.find((item) => item.id === attack.weapon)?.name ?? attack.weapon}: {formatRemaining(Math.max(0, Date.parse(attack.due_at) - constructionNow))}</span>
              ))}
            </div>
          ) : selectedBuilding ? (
            <div className="inspector-card">
              <strong>
                {selectedBuilding.name}, уровень {selectedBuilding.level}
              </strong>
              <span>Здоровье {selectedBuilding.health}/{selectedBuildingMaxHealth}</span>
              <span>Поворот: {(selectedBuilding.rotation ?? 0) * 90}°</span>
              <span className="building-owner">Владелец: <Star size={15} aria-label="Уровень" /> {ownerLevel ?? '—'} · {ownerName ?? 'Игрок'}</span>
              {!canManageSelectedBuilding ? <span>Чужая постройка: управление недоступно</span> : null}
              <span>Состояние: {selectedBuilding.state === 'ruined' ? 'разрушена' : selectedBuilding.status === 'construction' ? 'строится' : selectedBuilding.state === 'damaged' ? 'повреждена' : 'работает'}</span>
              {selectedBuilding.kind === 'oil_well' ? (
                <>
                  <span>Запас нефти: {selectedOilNode ? `${selectedOilNode.amount.toLocaleString('ru-RU')}/${selectedOilNode.maxAmount.toLocaleString('ru-RU')}` : 'загрузка'}</span>
                  <span>Добыча: {selectedBuilding.level === 1 ? '100 нефти за 30 мин. · 15 рабочих' : selectedBuilding.level === 2 ? '250 нефти за 25 мин. · 21 рабочий' : '400 нефти за 60 мин. · 27 рабочих'}</span>
                  {selectedOilJob ? <span>{selectedOilJob.state === 'ready' ? 'Добыча завершена — соберите нефть' : `До конца добычи: ${formatRemaining(Math.max(0, Date.parse(selectedOilJob.completes_at) - constructionNow))}`}</span> : null}
                  {canManageSelectedBuilding && selectedBuilding.status === 'active' ? <span>Запустить добычу или собрать нефть можно нажатием на вышку либо в панели «Производство».</span> : null}
                </>
              ) : null}
              {['defense_cannon', 'defense_bolt_thrower', 'defense_storm_coil'].includes(selectedBuilding.kind) ? (
                <>
                  <span>Радиус: {selectedBuilding.cannonRange ?? '—'} кл. · Урон: {selectedBuilding.cannonDamage ?? '—'}</span>
                  {canManageSelectedBuilding ? (
                    <>
                      <span>Перезарядка: {selectedBuilding.cannonCooldownSeconds ?? 12} с · Гарнизон: {selectedBuilding.cannonEnabled ? '1 житель' : 'нет'}</span>
                      {selectedBuilding.cannonAmmo ? <span>Заряды: {cannonCharges} ({selectedBuilding.cannonAmmo === 'explosives' ? 'взрывчатка' : selectedBuilding.cannonAmmo === 'fuel' ? 'бензин' : 'камень'})</span> : <span>Боеприпасы не требуются</span>}
                      <span>Автоатака: {selectedBuilding.cannonEnabled ? cannonIdleReason ?? 'включена' : 'выключена'}</span>
                      {selectedBuilding.cannonTargetId ? <span>Последняя цель: {selectedBuilding.cannonTargetId}</span> : null}
                      {selectedBuilding.cannonEnabled && selectedBuilding.cannonNextAttackAt && selectedBuilding.cannonNextAttackAt > constructionNow ? <span>До выстрела: {formatRemaining(selectedBuilding.cannonNextAttackAt - constructionNow)}</span> : null}
                    </>
                  ) : null}
                </>
              ) : null}
              {['defense_stakes', 'defense_resin_snare'].includes(selectedBuilding.kind) ? (
                <>
                  <span>Урон при входе: {selectedBuilding.trapDamage ?? '—'}</span>
                  <span>Заряды: {selectedBuilding.trapCharges ?? 0}/{selectedBuilding.trapMaxCharges ?? '—'}</span>
                  {selectedBuilding.kind === 'defense_resin_snare' ? <span>Замедляет следующий шаг монстра в 1,5 раза</span> : null}
                </>
              ) : null}
              {['defense_automaton_bay', 'defense_guardian_enclosure'].includes(selectedBuilding.kind) ? (
                <>
                  <span>Слотов защитников: {selectedBuilding.defenseSlots ?? '—'}</span>
                  <span>Радиус патруля: {selectedBuilding.defensePatrolRadius ?? '—'} кл.</span>
                  <span>Для работы нужен {selectedBuilding.defenseStaffRole === 'mechanic' ? 'механик' : 'смотритель'}</span>
                  <span>Создание защитников пока недоступно</span>
                </>
              ) : null}
              {selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>До завершения: {formatRemaining(selectedBuilding.completesAt - constructionNow)}</span> : null}
              {selectedFieldSpec && selectedBuilding.status === 'active' && selectedFieldStage > 0 ? (
                <>
                  <span>Фаза роста: {selectedFieldStage}/{selectedFieldMaxStage}{selectedBuilding.isSuperCrop ? ' · супер-цикл' : ''}</span>
                  {selectedFieldReadyToHarvest ? <span>Урожай готов к сбору</span> : null}
                  {selectedFieldReadyToAdvance ? <span>Фаза завершена, нужна команда на рост</span> : null}
                  {!selectedFieldStageReady && selectedFieldNextAt ? <span>До конца фазы: {formatRemaining(selectedFieldNextAt - constructionNow)}</span> : null}
                </>
              ) : null}
              {canManageSelectedBuilding && selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>Мгновенно: {rushCost} крист.</span> : null}
              {canManageSelectedBuilding && selectedBuilding.status === 'construction' && rushCost > 0 && crystals < rushCost ? <small className="upgrade-error">Не хватает эолийских кристаллов: {crystals}/{rushCost}</small> : null}
              {canManageSelectedBuilding && !selectedBuilding.kind.startsWith('ruins_') ? <span>Улучшение выполняется из меню этой постройки.</span> : null}
              <HealthBar health={selectedBuilding.health} maxHealth={selectedBuildingMaxHealth} />
              {modelPreviewOpen ? <BuildingModelPreview building={selectedBuilding} className="inspector-model-preview" /> : null}
              {constructionError ? <small className="upgrade-error" role="alert">{constructionError}</small> : null}
              {cannonError ? <small className="upgrade-error" role="alert">{cannonError}</small> : null}
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
            {canManageSelectedBuilding ? <IconButton label="Улучшить" icon={TrendingUp} disabled={selectedBuilding.status !== 'active' || nextUpgrades.length === 0} onClick={() => setUpgradeOpen(true)} /> : null}
            {canManageSelectedBuilding && ['defense_cannon', 'defense_bolt_thrower', 'defense_storm_coil'].includes(selectedBuilding.kind) ? (
              <IconButton
                label={selectedBuilding.kind === 'defense_cannon'
                  ? selectedBuilding.cannonEnabled ? 'Выключить пушку' : 'Включить пушку'
                  : selectedBuilding.cannonEnabled ? 'Выключить орудие' : 'Включить орудие'}
                icon={Shield}
                active={Boolean(selectedBuilding.cannonEnabled)}
                disabled={cannonMutation.isPending || (!selectedBuilding.cannonEnabled && (selectedBuilding.status !== 'active' || selectedBuilding.state === 'ruined'))}
                onClick={() => { setCannonError(''); cannonMutation.mutate({ id: selectedBuilding.id, enabled: !selectedBuilding.cannonEnabled }) }}
              />
            ) : null}
            {canManageSelectedBuilding && ['defense_stakes', 'defense_resin_snare'].includes(selectedBuilding.kind) ? (
              <IconButton label="Перезарядить ловушку" icon={Shield}
                disabled={trapMutation.isPending || selectedBuilding.status !== 'active' || selectedBuilding.state === 'ruined' || (selectedBuilding.trapCharges ?? 0) >= (selectedBuilding.trapMaxCharges ?? 0)}
                onClick={() => { setCannonError(''); trapMutation.mutate(selectedBuilding.id) }} />
            ) : null}
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
            {canManageSelectedBuilding && selectedBuilding.status === 'construction' ? (
              <IconButton label="Отменить строительство" icon={Trash2} disabled={cancelConstructionMutation.isPending}
                onClick={() => cancelConstructionMutation.mutate(selectedBuilding.id)} />
            ) : null}
            {canManageSelectedBuilding && (selectedBuilding.state === 'active' || selectedBuilding.state === 'damaged') && selectedBuilding.health < selectedBuildingMaxHealth ? (
              <IconButton label="Починить" icon={Hammer} disabled={repairMutation.isPending}
                onClick={() => repairMutation.mutate(selectedBuilding.id)} />
            ) : null}
            {canManageSelectedBuilding && (selectedBuilding.state === 'active' || selectedBuilding.state === 'damaged') && !selectedBuilding.kind.startsWith('ruins_') && selectedBuilding.kind !== 'oil_well' ? (
              <>
                <IconButton label={relocatingBuildingId === selectedBuilding.id ? 'Отменить перенос' : 'Переместить'} icon={Move}
                  active={relocatingBuildingId === selectedBuilding.id}
                  onClick={() => setRelocatingBuildingId(relocatingBuildingId === selectedBuilding.id ? null : selectedBuilding.id)} />
                <IconButton label="Повернуть на 90°" icon={RotateCw} disabled={rotateMutation.isPending}
                  onClick={() => rotateMutation.mutate(selectedBuilding)} />
              </>
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
                label={selectedBuilding.kind === 'oil_well' || selectedBuilding.kind.startsWith('ruins_') ? 'Продать' : 'Удалить'}
                icon={Trash2}
                onClick={() => { deleteMutation.reset(); setDeleteOpen(true) }}
              />
            ) : null}
            {selectedBuildingHasModel ? (
              <IconButton
                label={modelPreviewOpen ? 'Скрыть 3D' : '3D preview'}
                icon={Box}
                active={modelPreviewOpen}
                sound={modelPreviewOpen ? 'ui.toggle.off' : 'ui.toggle.on'}
                onClick={() => setModelPreviewOpen((current) => !current)}
              />
            ) : null}
          </>
        ) : null}
        <IconButton label="Построить" icon={Hammer} active={tool === 'build'} disabled={!activeTile} sound="ui.panel.open" onClick={() => setBuildMenuOpen(true)} />
        <IconButton label="Маршрут" icon={Route} active={tool === 'road'} disabled={!activeTile} onClick={() => setTool('road')} />
        <IconButton label="Рейд" icon={Swords} active={tool === 'raid'} disabled={!activeTile} onClick={() => setTool('raid')} />
      </div>
      {createPortal(<Modal title="Оружие против монстра" open={weaponMenuOpen && Boolean(selectedMonster)} onClose={() => { if (!attackMonsterMutation.isPending) setWeaponMenuOpen(false) }} className="weapon-menu-modal">
        <div className="weapon-menu-list" role="radiogroup" aria-label="Выбрать оружие">
          {weaponCatalog.map((item) => {
            const count = inventoryAmount(inventoryQuery.data?.inventory.items, item.id)
            const selected = item.id === (availableWeapons.some((weapon) => weapon.id === selectedWeapon) ? selectedWeapon : availableWeapons[0]?.id)
            return (
              <button key={item.id} type="button" role="radio" aria-checked={selected} className={`weapon-menu-item${selected ? ' weapon-menu-item-selected' : ''}`} disabled={count === 0 || attackMonsterMutation.isPending} onClick={() => setSelectedWeapon(item.id)}>
                <ResourceIcon id={item.id} label={item.name} />
                <span className="weapon-menu-name">{item.name}</span>
                <span className="weapon-menu-time">{weaponFuseLabel(item.id)}</span>
                <span className="weapon-menu-count">×{count}</span>
              </button>
            )
          })}
        </div>
        {availableWeapons.length === 0 ? <p>В инвентаре нет оружия. Его можно изготовить в производственных постройках.</p> : null}
        <div className="weapon-menu-actions">
          <button className="text-button" type="button" disabled={attackMonsterMutation.isPending} onClick={() => setWeaponMenuOpen(false)}>Отмена</button>
          <button className="text-button text-button-primary" type="button" disabled={attackMonsterMutation.isPending || availableWeapons.length === 0 || !selectedMonster} onClick={() => {
            if (selectedMonster) attackMonsterMutation.mutate({ monsterId: selectedMonster.id, weaponId: availableWeapons.some((item) => item.id === selectedWeapon) ? selectedWeapon : availableWeapons[0]!.id })
          }}>Применить оружие</button>
        </div>
      </Modal>, document.body)}
      <UpgradeModal
        building={selectedBuilding}
        upgrades={nextUpgrades}
        open={upgradeOpen}
        pending={upgradeMutation.isPending}
        error={upgradeError}
        onClose={() => {
          setUpgradeOpen(false)
          setUpgradeError('')
        }}
        onUpgrade={(targetType) => {
          if (selectedBuilding) {
            setUpgradeError('')
            upgradeMutation.mutate({ buildingId: selectedBuilding.id, targetType })
          }
        }}
      />
      <Modal title={selectedBuilding?.kind === 'oil_well' ? 'Продать нефтяную вышку' : selectedBuilding?.kind.startsWith('ruins_') ? 'Продать руину' : 'Подтвердите снос'} open={deleteOpen && canManageSelectedBuilding} onClose={() => { if (!deleteMutation.isPending) setDeleteOpen(false) }}>
        <div className="upgrade-dialog">
          <p>{selectedBuilding?.kind === 'oil_well' || selectedBuilding?.kind.startsWith('ruins_') ? 'Продать' : 'Удалить'} «{selectedBuilding?.name}»? Действие нельзя отменить. Текущая работа прекратится.</p>
          <p>Возврат: {selectedBuilding?.demolitionRefundCoins ?? 0} монет. Другие ресурсы не возвращаются.</p>
          <div className="upgrade-actions">
            <button className="text-button" type="button" disabled={deleteMutation.isPending} onClick={() => setDeleteOpen(false)}>Отмена</button>
            <button className="text-button text-button-primary" type="button" disabled={deleteMutation.isPending || !selectedBuilding} onClick={() => { if (selectedBuilding) deleteMutation.mutate(selectedBuilding.id) }}>{selectedBuilding?.kind === 'oil_well' ? 'Продать вышку' : selectedBuilding?.kind.startsWith('ruins_') ? 'Продать руину' : 'Удалить постройку'}</button>
          </div>
          {deleteMutation.isError ? <p className="upgrade-error" role="alert">{deleteMutation.error instanceof Error ? deleteMutation.error.message : 'Не удалось удалить постройку'}</p> : null}
        </div>
      </Modal>
    </aside>
  )
}

function UpgradeModal({
  building,
  upgrades,
  open,
  pending,
  error,
  onClose,
  onUpgrade,
}: {
  building: PlacedBuilding | null
  upgrades: UpgradeInfo[]
  open: boolean
  pending: boolean
  error: string
  onClose: () => void
  onUpgrade: (targetType?: BuildingKind) => void
}) {
  if (!building || upgrades.length === 0) {
    return null
  }
  if (upgrades.length > 1) {
    return (
      <Modal title="Выбор ветки улучшения" open={open} onClose={onClose} className="upgrade-branch-modal">
        <p>Каменный дом уровня 6 можно улучшить по одной из двух веток. Выбранный дом продолжит развиваться только в своей ветке.</p>
        <div className="upgrade-branch-options">
          {upgrades.map((option) => {
            const preview = upgradePreviewAsset(building, option)
            return <article className="upgrade-branch-card" key={option.type}>
              <div className={`upgrade-preview build-icon-${option.type}`}>
                {preview ? <img src={preview} alt={`Модель: ${option.name}, уровень ${option.level}`} draggable={false} /> : <TrendingUp size={34} aria-hidden="true" />}
              </div>
              <h3>{option.name}</h3>
              <span>Уровень {option.level} · HP {option.health} · {formatDuration(option.buildSeconds)}</span>
              <div className="upgrade-branch-cost">{option.cost.map((cost) => <em key={cost.resource}><ResourceIcon id={cost.resource} label={resourceLabel(cost.resource)} />{cost.amount}</em>)}</div>
              <button className="text-button text-button-primary" type="button" disabled={pending} onClick={() => onUpgrade(option.type)}>Улучшить до {option.name}</button>
            </article>
          })}
        </div>
        {error ? <p className="upgrade-error" role="alert">{error}</p> : null}
      </Modal>
    )
  }
  const nextUpgrade = upgrades[0]!
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
          <button className="text-button text-button-primary" type="button" disabled={pending} onClick={() => onUpgrade()}>
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
    fiber: 'Волокно',
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

function getNextUpgrades(building: PlacedBuilding): UpgradeInfo[] {
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  if (!spec) {
    return []
  }
  const nextLevel = spec.upgradeLevels?.find((level) => level.level === building.level + 1)
  if (nextLevel) {
    return [{
      type: spec.type as BuildingKind,
      name: spec.name,
      level: nextLevel.level,
      buildSeconds: nextLevel.buildSeconds,
      population: nextLevel.population,
      health: nextLevel.health,
      footprint: spec.footprint,
      cost: [...nextLevel.cost],
    }]
  }
  const finalLevel = spec.upgradeLevels?.find((level) => level.level === building.level && level.nextType)
  const nextTypes = finalLevel?.nextType ? [finalLevel.nextType] : spec.upgradeTo
  return nextTypes.flatMap((nextType) => {
    const nextSpec = buildingCatalog.find((item) => item.type === nextType)
    return nextSpec ? [{
      type: nextSpec.type as BuildingKind, name: nextSpec.name, level: nextSpec.level,
      buildSeconds: nextSpec.buildSeconds, population: nextSpec.population,
      health: nextSpec.health ?? 100, footprint: nextSpec.footprint, cost: [...nextSpec.cost],
    }] : []
  })
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
    comparisons.push({ label: 'Строители', before: String(current.population), after: String(nextUpgrade.population) })
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

const ruinTypeLabels: Record<string, string> = {
  ruins_town_square: 'Старая ратушная площадь',
  ruins_archive: 'Архив чертежей',
  ruins_mint: 'Монетный двор',
  ruins_storage: 'Старый складской узел',
  ruins_greenhouse: 'Заросшая оранжерея',
  ruins_water_station: 'Водяная станция',
  ruins_bastion: 'Каменный бастион',
  ruins_mechanic_workshop: 'Мастерская механизмов',
  ruins_wind_shrine: 'Святилище ветра',
  ruins_ore_obelisk: 'Залежный обелиск',
  ruins_rift_watch: 'Разломная сторожевая',
  ruins_river_lighthouse: 'Речной маяк',
}

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
