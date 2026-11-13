import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { ReactNode } from 'react'
import { Box, ChevronDown, ChevronUp, Gem, Repair, Move, RotateCw, Shield, Sprout, Star, Swords, Trash2, TrendingUp } from '../../shared/ui/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getRepairStatus } from '../../shared/api/buildings'
import { playUiSound } from '../../audio/playUiSound'
import { playCombatSound } from '../../audio/voiceManager'
import { cellLabel } from '../../game/coordinates/district'
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
import { advanceField, harvestField, patchResourceNode, type InventoryResponse } from '../../shared/api/economy'
import { createAttackMonster, getCombatRules, listPendingWeaponAttacks, useWeaponOnBuilding, useWeaponOnMonster, toMonster, type MonsterLootResponse, type MonsterResponse, type PendingWeaponAttack } from '../../shared/api/monsters'
import { weaponFuseLabel } from './weaponFuse'
import { IconButton, Modal, Tabs } from '../../shared/ui'
import { formatRemaining } from '../../shared/time/formatRemaining'
import { useAuthStore } from '../auth/useAuthStore'
import { useOwnershipContext } from '../alliance/useOwnership'
import { ownershipOf } from '../../shared/ui/ownership'
import { ObjectMarks } from '../../shared/ui/ObjectMarks'
import { getPublicPlayer } from '../auth/api'
import { inventoryAmount, useInventory } from '../economy/useInventory'
import { useProductionJobs } from '../production/useProductionJobs'
import { fieldHarvestSound, playConfirmedCoinChange, playConfirmedRareReward, resourceGatherSound } from '../economy/economyAudio'
import { fieldCropSpec } from '../fields/fieldGrowth'
import { ResourceIcon } from '../resources/ResourceIcon'
import { useThreatLevel } from '../threat/ThreatPanel'
import { showToast } from '../notifications/toast'
import { PublicProfileButton } from '../player/PublicProfileButton'
import { PlayerName } from '../player/PlayerName'

type InspectorTab = 'tile' | 'object'

const tabs = [
  { id: 'tile', label: 'Клетка' },
  { id: 'object', label: 'Объект' },
] as const

export function Inspector() {
  const ownership = useOwnershipContext()
  const [expanded, setExpanded] = useState(false)
  const disclosure = useRef<HTMLButtonElement>(null)
  const [activeTab, setActiveTab] = useState<InspectorTab>('tile')
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [repairOpen, setRepairOpen] = useState(false)
  const [modelPreviewOpen, setModelPreviewOpen] = useState(false)
  const [upgradeError, setUpgradeError] = useState('')
  const [constructionError, setConstructionError] = useState('')
  const [cannonError, setCannonError] = useState('')
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [selectedWeapon, setSelectedWeapon] = useState('throwing_knives')
  const [weaponMenuOpen, setWeaponMenuOpen] = useState(false)
  const [summonMenuOpen, setSummonMenuOpen] = useState(false)
  const selectedTile = useGameStore((state) => state.selectedTile)
  const hoveredTile = useGameStore((state) => state.hoveredTile)
  const buildings = useGameStore((state) => state.buildings)
  const resourceNodes = useGameStore((state) => state.resourceNodes)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const repairMenuBuildingId = useGameStore((state) => state.repairMenuBuildingId)
  const setRepairMenuBuildingId = useGameStore((state) => state.setRepairMenuBuildingId)
  const buildingActionRequest = useGameStore((state) => state.buildingActionRequest)
  const setBuildingActionRequest = useGameStore((state) => state.setBuildingActionRequest)
  const relocatingBuildingId = useGameStore((state) => state.relocatingBuildingId)
  const setRelocatingBuildingId = useGameStore((state) => state.setRelocatingBuildingId)
  const selectedMonsterId = useGameStore((state) => state.selectedMonsterId)
  const constructionNow = useGameStore((state) => state.constructionNow)
  const damageEvents = useGameStore(state => state.buildingDamageEvents)
  const tool = useGameStore((state) => state.tool)
  useEffect(() => { if (tool === 'build') setExpanded(false) }, [tool])
  useEffect(() => { setRepairOpen(false) }, [selectedBuildingId])
  useEffect(() => {
    if (!repairMenuBuildingId) return
    if (repairMenuBuildingId === selectedBuildingId) setRepairOpen(true)
    setRepairMenuBuildingId(null)
  }, [repairMenuBuildingId, selectedBuildingId, setRepairMenuBuildingId])
  useEffect(() => {
    if (!buildingActionRequest) return
    if (buildingActionRequest.buildingId === selectedBuildingId) {
      setActiveTab('object')
      if (buildingActionRequest.action === 'repair') setRepairOpen(true)
      if (buildingActionRequest.action === 'upgrade') setUpgradeOpen(true)
      if (buildingActionRequest.action === 'attack') setWeaponMenuOpen(true)
    }
    setBuildingActionRequest(null)
  }, [buildingActionRequest, selectedBuildingId, setBuildingActionRequest])
  const setTool = useGameStore((state) => state.setTool)
  const deleteBuilding = useGameStore((state) => state.deleteBuilding)
  const addBuilding = useGameStore((state) => state.addBuilding)
  const upsertResourceNode = useGameStore((state) => state.upsertResourceNode)
  const upsertMonster = useGameStore((state) => state.upsertMonster)
  const worldTiles = useGameStore((state) => state.worldTiles)
  const queryClient = useQueryClient()
  const inventoryQuery = useInventory()
  const player = useAuthStore((state) => state.player)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const pendingWeaponsQuery = useQuery({
    queryKey: ['combat', 'attacks'],
    queryFn: listPendingWeaponAttacks,
    enabled: Boolean(player),
    refetchInterval: (query) => query.state.data?.attacks.length ? 5000 : realtimeStatus === 'connected' ? 30_000 : 10_000,
  })
  const oilJobsQuery = useProductionJobs(Boolean(player))
  const activeTile = selectedTile ?? hoveredTile
  const selectedBuilding = buildings.find((building) => building.id === selectedBuildingId) ?? null
  const canManageSelectedBuilding = Boolean(selectedBuilding && player && selectedBuilding.owner === player.id)
  const canAttackSelectedBuilding = Boolean(selectedBuilding && player && selectedBuilding.owner !== player.id && selectedBuilding.health > 0 && ['active', 'damaged'].includes(selectedBuilding.state ?? ''))
  const combatRulesQuery = useQuery({ queryKey: ['combat', 'rules'], queryFn: getCombatRules, enabled: canAttackSelectedBuilding, staleTime: 60_000 })
  const ownerQuery = useQuery({
    queryKey: ['players', 'public', selectedBuilding?.owner],
    queryFn: () => getPublicPlayer(selectedBuilding!.owner),
    enabled: Boolean(selectedBuilding?.owner && selectedBuilding.owner !== player?.id),
    staleTime: 60_000,
    retry: false,
  })
  const ownerName = canManageSelectedBuilding ? player?.profile.display_name || player?.name : ownerQuery.data?.display_name
  const ownerLevel = canManageSelectedBuilding ? player?.profile.level : ownerQuery.data?.level
  const repairQuery = useQuery({
    queryKey: ['repairs', selectedBuilding?.id], queryFn: () => getRepairStatus(selectedBuilding!.id),
    enabled: Boolean(selectedBuilding && canManageSelectedBuilding && selectedBuilding.state !== 'ruined' && selectedBuilding.status !== 'construction'),
    refetchInterval: 5000, retry: false,
  })
  const selectedMonster = useGameStore((state) => state.monsters.find((monster) => monster.id === selectedMonsterId) ?? null)
  const inspectorTabs = selectedBuilding || selectedMonster ? tabs : [tabs[0]]
  useEffect(() => {
    if (activeTab === 'object' && !selectedBuilding && !selectedMonster) setActiveTab('tile')
  }, [activeTab, selectedBuilding, selectedMonster])
  const threat = useThreatLevel()
  const nextUpgrades = selectedBuilding && canManageSelectedBuilding ? getNextUpgrades(selectedBuilding) : []
  const selectedBuildingHasModel = selectedBuilding ? canResolveBuildingModelAsset(selectedBuilding) : false
  const selectedBuildingMaxHealth = selectedBuilding ? maxHealthForBuilding(selectedBuilding) : 100
  const rushCost = selectedBuilding?.status === 'construction' && selectedBuilding.state !== 'repairing' && selectedBuilding.completesAt ? rushCompletionCrystalCost(selectedBuilding.completesAt - constructionNow) : 0
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
  const terrainClass = selectedWorldTile ? `terrain-${selectedWorldTile.terrain}` : 'terrain-unknown'
  const canAttackTarget = Boolean(selectedMonster || canAttackSelectedBuilding)
  const selectedResourceNode = activeTile ? resourceNodes.find((node) => node.tile.x === activeTile.x && node.tile.y === activeTile.y && (node.resource !== 'oil' || node.state !== 'depleted')) ?? null : null
  const selectedOwnership = ownershipOf(selectedBuilding?.owner ?? selectedMonster?.creatorId ?? selectedResourceNode?.ownerId, ownership.viewerId, ownership.alliedIds)
  const objectThreat = Boolean(selectedMonster && ['aggro', 'chase', 'investigate', 'attacking', 'windup', 'recover'].includes(selectedMonster.state)) || Boolean(selectedBuilding && damageEvents.some(event => event.buildingId === selectedBuilding.id && constructionNow - event.createdAt < 1500))
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
        playBuildingSound('build.repair.started', result.building.id, 'repair_started')
        void queryClient.invalidateQueries({ queryKey: ['repairs', result.building.id] })
        void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
        void queryClient.invalidateQueries({ queryKey: ['economy', 'population'] })
        addBuilding(toPlacedBuilding(result.building))
      }
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      setRepairOpen(false)
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
  const selectedBuildingAttacks = pendingWeaponsQuery.data?.attacks.filter((attack) => attack.building_id === selectedBuildingId) ?? []
  const attackBuildingMutation = useMutation({
    mutationFn: ({ id, weapon }: { id: string; weapon: string }) => useWeaponOnBuilding(id, weapon),
    onSuccess: (result) => {
      setWeaponMenuOpen(false)
      if (result.building) {
        if (result.building.state === 'ruined' && (result.building.type === 'oil_well' || result.building.type.startsWith('ruins_'))) deleteBuilding(result.building.id)
        else addBuilding(toPlacedBuilding(result.building))
      }
      showToast('info', result.building ? 'Попадание подтверждено' : 'Заряд установлен на постройке')
      void queryClient.invalidateQueries({ queryKey: ['buildings'] })
      void queryClient.invalidateQueries({ queryKey: ['combat', 'attacks'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
    },
    onError: (error) => showToast('warning', formatActionError(error)),
  })
  const createMonsterMutation = useMutation({
    mutationFn: createAttackMonster,
    onSuccess: ({ monster }) => {
      setSummonMenuOpen(false)
      upsertMonster(toMonster(monster))
      void queryClient.invalidateQueries({ queryKey: ['monsters'] })
      void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
      showToast('info', 'Монстр создан. Он атакует чужие постройки поблизости.')
    },
    onError: (error) => showToast('warning', formatActionError(error)),
  })
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

  useEffect(() => {
    setUpgradeOpen(false)
    setDeleteOpen(false)
    setWeaponMenuOpen(false)
    setModelPreviewOpen(false)
    setSummonMenuOpen(false)
    setUpgradeError('')
    setConstructionError('')
  }, [selectedBuilding?.id, selectedMonster?.id])

  return (
    <aside id="game-inspector" tabIndex={-1} className={`inspector${expanded ? ' inspector-expanded' : ' inspector-collapsed'}${selectedMonster ? ' inspector-monster' : ''}`} aria-label="Инспектор" onKeyDown={(event) => {
      if (event.key === 'Escape' && expanded) { event.preventDefault(); event.stopPropagation(); setExpanded(false); disclosure.current?.focus() }
    }}>
      <div className="inspector-header">
        <div className="inspector-heading">
          <h2>{selectedMonster ? monsterName(selectedMonster.type) : selectedBuilding ? selectedBuilding.name : activeTile ? `Клетка ${cellLabel(activeTile)}` : 'Карта мира'}</h2>
          {!selectedMonster && !selectedBuilding && activeTile ? <small className={`inspector-terrain ${terrainClass}`}>{terrainLabel}</small> : null}
        </div>
        <button ref={disclosure} className="icon-button" type="button" aria-label={expanded ? 'Свернуть инспектор' : 'Развернуть инспектор'} title={expanded ? 'Свернуть инспектор' : 'Развернуть инспектор'} aria-expanded={expanded} aria-controls="inspector-details" data-audio-handled="true" onClick={() => { playUiSound(expanded ? 'ui.toggle.off' : 'ui.toggle.on'); setExpanded(!expanded) }}>
          {expanded ? <ChevronDown size={20} aria-hidden="true" /> : <ChevronUp size={20} aria-hidden="true" />}
        </button>
      </div>
      {selectedBuildingId && !selectedBuilding || selectedMonsterId && !selectedMonster ? <p className="inspector-target-status" role="status">Выбранный объект больше не доступен в загруженной области. Выберите цель заново.</p> : null}
      <div id="inspector-details" className="inspector-details">
      {(selectedBuilding || selectedMonster || selectedResourceNode) && <ObjectMarks ownership={selectedOwnership} selected threat={objectThreat}
        category={selectedBuilding ? buildingCatalog.find(item => item.type === selectedBuilding.kind)?.category : undefined}
        status={selectedBuilding ? selectedBuilding.state === 'building' || selectedBuilding.state === 'repairing' ? 'building' : selectedBuilding.health < selectedBuildingMaxHealth ? 'damage' : 'ready' : selectedResourceNode?.state === 'depleted' ? 'depleted' : undefined}
        rare={Boolean(selectedResourceNode && resourceCatalog.find(item => item.id === selectedResourceNode.resource)?.category === 'rare')} />}
      <section className="inspector-context" aria-label="Действие с целью">
        <strong>{selectedMonster ? 'Угроза' : selectedBuilding ? canManageSelectedBuilding ? 'Ваша постройка' : selectedOwnership === 'ally' ? 'Союзная постройка' : selectedOwnership === 'neutral' ? 'Нейтральная постройка' : 'Чужая постройка' : selectedResourceNode ? 'Ресурсный узел' : selectedRuin ? 'Руины' : 'Участок мира'}</strong>
        {selectedMonster || canAttackSelectedBuilding ? <button type="button" onClick={() => setWeaponMenuOpen(true)}>Выбрать оружие</button>
          : selectedBuilding ? canManageSelectedBuilding && selectedBuilding.status === 'active' && nextUpgrades.length > 0
            ? <button type="button" onClick={() => setUpgradeOpen(true)}>Открыть улучшение</button>
            : <button type="button" onClick={() => setActiveTab('object')}>Осмотреть постройку</button>
          : selectedResourceNode && selectedResourceNode.resource !== 'oil' ? <>
            <button type="button" disabled={resourceMutation.isPending || selectedResourceNode.state === 'depleted' || (selectedResourceNode.state === 'claimed' && selectedResourceNode.ownerId !== player?.id)} onClick={() => resourceMutation.mutate({ id: selectedResourceNode.id, action: selectedResourceNode.state === 'neutral' ? 'claim' : 'harvest' })}>{selectedResourceNode.state === 'neutral' ? 'Захватить узел' : 'Собрать ресурс'}</button>
            <small>{selectedResourceNode.state === 'depleted' ? 'Узел истощён. Дождитесь восстановления.' : selectedResourceNode.state === 'claimed' && selectedResourceNode.ownerId !== player?.id ? 'Узел принадлежит другому игроку.' : `Доступно: ${selectedResourceNode.amount}/${selectedResourceNode.maxAmount}`}</small>
          </> : selectedRuin ? <button type="button" disabled={ruinOccupied || ruinMutation.isPending} onClick={() => ruinMutation.mutate()}>{ruinOccupied ? 'Восстановление недоступно' : 'Захватить и восстановить'}</button>
          : null}
        {!activeTile && !selectedBuilding && !selectedMonster ? <small>Выберите клетку или объект на карте.</small> : null}
        {selectedBuilding ? <small>Здоровье {selectedBuilding.health}/{selectedBuildingMaxHealth}. {selectedBuilding.state === 'repairing' ? 'Ремонт: оставшееся время во вкладке «Объект».' : selectedBuilding.status === 'construction' ? 'Строительство: управление и срок во вкладке «Объект».' : canManageSelectedBuilding && !nextUpgrades.length ? 'Следующий уровень улучшения недоступен.' : ''}</small> : null}
        {selectedRuin && !selectedBuilding ? <small>Восстановление: {selectedRuin.hours} ч · {selectedRuin.coins.toLocaleString('ru-RU')} монет.</small> : null}
        {selectedBuilding && !canManageSelectedBuilding && !canAttackSelectedBuilding ? <small>Атака доступна только по действующей уязвимой постройке.</small> : null}
        {resourceMutation.error || ruinMutation.error ? <p role="alert">{(resourceMutation.error ?? ruinMutation.error)?.message}</p> : null}
      </section>
      <Tabs items={inspectorTabs} active={activeTab} onChange={setActiveTab}>
        {activeTab === 'tile' ? (
          <>
            <dl>
              <dt>Статус</dt>
              <dd>{activeTile ? 'Клетка выбрана' : 'Выберите клетку на карте'}</dd>
              {selectedWorldTile?.terrain === 'forest' ? (
                <>
                  <dt>Густота леса</dt>
                  <dd>{selectedWorldTile.forest_density}/3</dd>
                </>
              ) : null}
              {selectedRuin ? (
                <>
                  <dt>Владение</dt>
                  <dd>{ruinOccupied ? 'Руина занята' : 'Свободна'}</dd>
                </>
              ) : null}
              {selectedResourceNode ? (
                <>
                  <dt>Ресурсный узел</dt>
                  <dd>{resourceLabel(selectedResourceNode.resource)} · {selectedResourceNode.amount}/{selectedResourceNode.maxAmount}</dd>
                  <dt>Состояние узла</dt>
                  <dd>{resourceStateLabel[selectedResourceNode.state]}</dd>
                  {selectedResourceNode.resource === 'oil' && selectedResourceNode.state === 'neutral' ? <dd>Постройте нефтяную вышку, чтобы занять месторождение.</dd> : null}
                </>
              ) : null}
              {threat ? (
                <>
                  <dt>Угроза</dt>
                  <dd>уровень {threat.level}</dd>
                </>
              ) : null}
            </dl>
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
              {selectedMonster.creatorId ? <span>Создатель: <PlayerName playerId={selectedMonster.creatorId} />. Наград за убийство нет.</span> : null}
              {selectedMonster.creatorId && selectedMonster.expiresAt ? <span>Исчезнет через {formatRemaining(Math.max(0, selectedMonster.expiresAt - constructionNow))}</span> : null}
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
              {selectedBuilding.owner ? <PublicProfileButton key={selectedBuilding.owner} playerId={selectedBuilding.owner} /> : null}
              {!canManageSelectedBuilding ? <span>Чужая постройка: управление недоступно</span> : null}
              <span>Состояние: {selectedBuilding.state === 'ruined' ? 'разрушена' : selectedBuilding.state === 'repairing' ? 'ремонтируется' : selectedBuilding.status === 'construction' ? 'строится' : selectedBuilding.state === 'damaged' ? 'повреждена' : 'работает'}</span>
              {selectedBuilding.kind === 'oil_well' ? (
                <>
                  <span>Запас нефти: {selectedOilNode ? `${selectedOilNode.amount.toLocaleString('ru-RU')}/${selectedOilNode.maxAmount.toLocaleString('ru-RU')}` : 'загрузка'}</span>
                  <span>Добыча: {selectedBuilding.level === 1 ? '100 нефти за 30 мин. · 15 рабочих' : selectedBuilding.level === 2 ? '250 нефти за 25 мин. · 21 рабочий' : '400 нефти за 60 мин. · 27 рабочих'} <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /></span>
                  {selectedOilJob ? <span>{selectedOilJob.state === 'ready' ? 'Добыча завершена — соберите нефть' : `До конца добычи: ${formatRemaining(Math.max(0, Date.parse(selectedOilJob.completes_at) - constructionNow))}`}</span> : null}
                  {canManageSelectedBuilding && selectedBuilding.status === 'active' ? <span>Запустить добычу или собрать нефть можно нажатием на вышку либо в панели «Производство».</span> : null}
                </>
              ) : null}
              {['defense_cannon', 'defense_bolt_thrower', 'defense_storm_coil'].includes(selectedBuilding.kind) ? (
                <>
                  <span>Радиус: {selectedBuilding.cannonRange ?? '—'} кл. · Урон: {selectedBuilding.cannonDamage ?? '—'}</span>
                  {canManageSelectedBuilding ? (
                    <>
                      <span>Перезарядка: {selectedBuilding.cannonCooldownSeconds ?? 12} с · Гарнизон: {selectedBuilding.cannonEnabled ? <>1 житель <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /></> : 'нет'}</span>
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
              {selectedBuilding.status === 'construction' && selectedBuilding.completesAt ? <span>{selectedBuilding.state === 'repairing' ? 'До конца ремонта: ' : 'До завершения: '}{formatRemaining(selectedBuilding.completesAt - constructionNow)}</span> : null}
              {selectedFieldSpec && selectedBuilding.status === 'active' && selectedFieldStage > 0 ? (
                <>
                  <span>Фаза роста: {selectedFieldStage}/{selectedFieldMaxStage}{selectedBuilding.isSuperCrop ? ' · супер-цикл' : ''}</span>
                  {selectedFieldReadyToHarvest ? <span>Урожай готов к сбору</span> : null}
                  {selectedFieldReadyToAdvance ? <span>Фаза завершена, нужна команда на рост</span> : null}
                  {!selectedFieldStageReady && selectedFieldNextAt ? <span>До конца фазы: {formatRemaining(selectedFieldNextAt - constructionNow)}</span> : null}
                </>
              ) : null}
              {canManageSelectedBuilding && selectedBuilding.status === 'construction' && selectedBuilding.state !== 'repairing' && selectedBuilding.completesAt ? <span>Мгновенно: {rushCost} крист.</span> : null}
              {canManageSelectedBuilding && selectedBuilding.status === 'construction' && selectedBuilding.state !== 'repairing' && rushCost > 0 && crystals < rushCost ? <small className="upgrade-error">Не хватает эолийских кристаллов: {crystals}/{rushCost}</small> : null}
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
      </Tabs>
      <div className="inspector-actions">
        {selectedBuilding ? (
          <>
            {canAttackSelectedBuilding ? <>
              <IconButton label="Атаковать оружием" icon={Swords} onClick={() => setWeaponMenuOpen(true)} />
              <button type="button" disabled={createMonsterMutation.isPending || !combatRulesQuery.data} onClick={() => setSummonMenuOpen(true)}>Создать монстра{combatRulesQuery.data ? ` · ${combatRulesQuery.data.rules.summon_cost_coins} монет` : ''}</button>
              {selectedBuildingAttacks.map((attack) => <span key={attack.id}>Заряд: {resourceCatalog.find((item) => item.id === attack.weapon)?.name ?? attack.weapon} — {formatRemaining(Math.max(0, Date.parse(attack.due_at) - constructionNow))}</span>)}
            </> : null}
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
            {canManageSelectedBuilding && selectedBuilding.status === 'construction' && selectedBuilding.state !== 'repairing' ? (
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
            {canManageSelectedBuilding && selectedBuilding.status === 'construction' && selectedBuilding.state !== 'repairing' ? (
              <IconButton label="Отменить строительство" icon={Trash2} disabled={cancelConstructionMutation.isPending}
                onClick={() => cancelConstructionMutation.mutate(selectedBuilding.id)} />
            ) : null}
            {canManageSelectedBuilding && (selectedBuilding.state === 'active' || selectedBuilding.state === 'damaged') && selectedBuilding.health < selectedBuildingMaxHealth ? (
              <IconButton label="Ремонт" icon={Repair} disabled={repairMutation.isPending}
                onClick={() => setRepairOpen(true)} />
            ) : null}
            {canManageSelectedBuilding && (selectedBuilding.state === 'active' || selectedBuilding.state === 'damaged') && !selectedBuilding.kind.startsWith('ruins_') && selectedBuilding.kind !== 'oil_well' ? (
              <>
                <IconButton label={relocatingBuildingId === selectedBuilding.id ? 'Отменить перенос' : 'Переместить'} icon={Move}
                  active={relocatingBuildingId === selectedBuilding.id}
                  onClick={() => setRelocatingBuildingId(relocatingBuildingId === selectedBuilding.id ? null : selectedBuilding.id)} />
                <IconButton label="Повернуть на 90°" icon={RotateCw} disabled={rotateMutation.isPending || relocatingBuildingId === selectedBuilding.id}
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
        {canAttackTarget ? <IconButton label="Атака" icon={Swords} active={tool === 'attack'} onClick={() => { setTool('attack'); setWeaponMenuOpen(true) }} /> : null}
      </div>
      {createPortal(<Modal title={selectedMonster ? 'Оружие против монстра' : 'Оружие против постройки'} open={weaponMenuOpen && (Boolean(selectedMonster) || canAttackSelectedBuilding)} onClose={() => { if (!attackMonsterMutation.isPending && !attackBuildingMutation.isPending) setWeaponMenuOpen(false) }} className="weapon-menu-modal">
        <div className="weapon-menu-list" role="radiogroup" aria-label="Выбрать оружие">
          {weaponCatalog.map((item) => {
            const count = inventoryAmount(inventoryQuery.data?.inventory.items, item.id)
            const selected = item.id === (availableWeapons.some((weapon) => weapon.id === selectedWeapon) ? selectedWeapon : availableWeapons[0]?.id)
            return (
              <button key={item.id} type="button" role="radio" aria-checked={selected} className={`weapon-menu-item${selected ? ' weapon-menu-item-selected' : ''}`} disabled={count === 0 || attackMonsterMutation.isPending || attackBuildingMutation.isPending} onClick={() => setSelectedWeapon(item.id)}>
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
          <button className="text-button" type="button" disabled={attackMonsterMutation.isPending || attackBuildingMutation.isPending} onClick={() => setWeaponMenuOpen(false)}>Отмена</button>
          <button className="text-button text-button-primary" type="button" disabled={attackMonsterMutation.isPending || attackBuildingMutation.isPending || availableWeapons.length === 0 || (!selectedMonster && !canAttackSelectedBuilding)} onClick={() => {
            const weapon = availableWeapons.some((item) => item.id === selectedWeapon) ? selectedWeapon : availableWeapons[0]!.id
            if (selectedMonster) attackMonsterMutation.mutate({ monsterId: selectedMonster.id, weaponId: weapon })
            else if (selectedBuilding && canAttackSelectedBuilding) attackBuildingMutation.mutate({ id: selectedBuilding.id, weapon })
          }}>Применить оружие</button>
        </div>
      </Modal>, document.body)}
      <Modal title="Создать монстра" open={summonMenuOpen && canAttackSelectedBuilding} onClose={() => { if (!createMonsterMutation.isPending) setSummonMenuOpen(false) }}>
        <p>Цена: {combatRulesQuery.data?.rules.summon_cost_coins} монет. Монстр атакует чужие постройки поблизости, включая постройки третьих игроков. Создателя он не атакует.</p>
        <p>Лимит: {combatRulesQuery.data?.rules.summon_max_alive}. Срок жизни: {Math.round((combatRulesQuery.data?.rules.summon_lifetime_seconds ?? 0) / 60)} мин. Повторное создание через {combatRulesQuery.data?.rules.summon_cooldown_seconds} с. Наград за убийство нет.</p>
        <button type="button" disabled={createMonsterMutation.isPending || !selectedBuilding || !combatRulesQuery.data} onClick={() => { if (selectedBuilding) createMonsterMutation.mutate(selectedBuilding.id) }}>Подтвердить создание</button>
        {createMonsterMutation.isError ? <p role="alert">{formatActionError(createMonsterMutation.error)}</p> : null}
      </Modal>
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
      {createPortal(<Modal title="Ремонт постройки" open={repairOpen && canManageSelectedBuilding && Boolean(selectedBuilding)} onClose={() => { if (!repairMutation.isPending) setRepairOpen(false) }} className="repair-modal">
        <div className="upgrade-dialog">
          <strong>{selectedBuilding?.name}</strong>
          {repairQuery.isPending ? <p role="status">Загружаем условия ремонта…</p> : null}
          {repairQuery.error ? <p role="alert">Условия ремонта не загружены. <button type="button" onClick={() => void repairQuery.refetch()}>Повторить</button></p> : null}
          {repairQuery.data?.repair.job ? (
            <p>Ремонт уже выполняется. Осталось {formatRemaining(Date.parse(repairQuery.data.repair.job.due_at) - constructionNow)}.</p>
          ) : repairQuery.data ? (
            <>
              <p>Время ремонта: {formatDuration(repairQuery.data.repair.duration_seconds)} · Рабочие: {repairQuery.data.repair.workers} <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /></p>
              <div className="upgrade-cost repair-cost">
                <span>Стоимость ремонта</span>
                {repairQuery.data.repair.cost.map((item) => <em key={item.resource} title={`${resourceLabel(item.resource)}: ${item.amount}`}><ResourceIcon id={item.resource} label={resourceLabel(item.resource)} />{item.amount}</em>)}
              </div>
            </>
          ) : null}
          <div className="upgrade-actions">
            <button className="text-button" type="button" disabled={repairMutation.isPending} onClick={() => setRepairOpen(false)}>Отмена</button>
            <button className="text-button text-button-primary" type="button" disabled={repairMutation.isPending || repairQuery.isPending || Boolean(repairQuery.error) || !repairQuery.data || Boolean(repairQuery.data.repair.job)} onClick={() => { if (selectedBuilding) repairMutation.mutate(selectedBuilding.id) }}>Отремонтировать</button>
          </div>
        </div>
      </Modal>, document.body)}
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
      </div>
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
  return createPortal(<Modal title="Улучшение постройки" open={open} onClose={onClose} className="upgrade-modal">
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
            <div className={item.label === 'Время работ' ? 'upgrade-stat-time' : undefined} key={item.label}>
              <dt>{item.label}{item.resource ? <> <ResourceIcon id={item.resource} label={resourceLabel(item.resource)} /></> : null}</dt>
              <dd>
                {item.before !== 'сейчас' ? <span className="upgrade-stat-before">{item.before}{['Работники', 'Население', 'Жители в доме'].includes(item.label) ? <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /> : null}</span> : null}
                <strong className="upgrade-stat-after">{item.after}{['Работники', 'Население', 'Жители в доме'].includes(item.label) ? <ResourceIcon id="population" label="Жители" className="resident-icon-inline" decorative /> : null}</strong>
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
    </Modal>, document.body)
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
  before: ReactNode
  after: ReactNode
  resource?: string
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
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  const comparisons: UpgradeComparison[] = [
    { label: 'Прочность', before: String(current.health), after: String(nextUpgrade.health) },
    { label: 'Время работ', before: 'сейчас', after: formatDuration(nextUpgrade.buildSeconds) },
  ]
  if (spec?.category === 'housing') {
    comparisons.push({ label: 'Жители в доме', before: `До: ${formatNumber(current.population)}`, after: `После: ${formatNumber(nextUpgrade.population)}` })
  } else if (building.kind === 'town_hall') {
    comparisons.push({ label: 'Лимит построек', before: String(buildingLimitForLevel(building.level)), after: String(buildingLimitForLevel(nextUpgrade.level)) })
  } else if (building.kind === 'coin_storage') {
    comparisons.push({ label: 'Вместимость', resource: 'coins', before: formatNumber(coinStorageCapacity(building.level)), after: formatNumber(coinStorageCapacity(nextUpgrade.level)) })
  } else if (spec?.category === 'fields') {
    const crop = fieldCropSpec(building.kind)
    const currentYield = crop?.rewardsByLevel[building.level - 1]
    const nextYield = crop?.rewardsByLevel[nextUpgrade.level - 1]
    if (currentYield && nextYield) {
      comparisons.push({ label: 'Урожай за сбор', before: formatFieldYield(currentYield), after: formatFieldYield(nextYield) })
    }
    if (current.population > 0 || nextUpgrade.population > 0) {
      comparisons.push({ label: 'Работники', before: String(current.population), after: String(nextUpgrade.population) })
    }
  } else if (current.population > 0 || nextUpgrade.population > 0) {
    comparisons.push({ label: 'Работники', before: String(current.population), after: String(nextUpgrade.population) })
  }
  return comparisons
}

function formatFieldYield(reward: NonNullable<ReturnType<typeof fieldCropSpec>>['rewardsByLevel'][number]) {
  const renderItems = (items: { resource: string; amount: number }[], coins?: number) => <span className="upgrade-yield-group">
    {coins !== undefined ? <span><ResourceIcon id="coins" label={resourceLabel('coins')} decorative />{formatNumber(coins)}</span> : null}
    {items.map((item) => <span key={item.resource}><ResourceIcon id={item.resource} label={resourceLabel(item.resource)} decorative />{formatNumber(item.amount)}</span>)}
  </span>
  return <span className="upgrade-yield">
    {renderItems(reward.rewards, reward.coins)}
    {reward.superRewards?.length ? <span className="upgrade-yield-bonus"><small>Редкий урожай</small>{renderItems(reward.superRewards, reward.superCoins)}</span> : null}
  </span>
}

const coinStorageCapacityByLevel = [2000, 5000, 10000, 25000, 60000, 150000, 350000, 800000, 1800000, 4000000, 9000000, 20000000]

function coinStorageCapacity(level: number) {
  return coinStorageCapacityByLevel[Math.max(0, Math.min(level, coinStorageCapacityByLevel.length) - 1)] ?? 0
}

function formatNumber(value: number) {
  return value.toLocaleString('ru-RU')
}

function getCurrentStats(building: PlacedBuilding) {
  const spec = buildingCatalog.find((item) => item.type === building.kind)
  const level = spec?.upgradeLevels?.find((item) => item.level === building.level)
  return {
    health: level?.health ?? spec?.health ?? building.health,
    population: level?.population ?? spec?.population ?? 0,
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
  investigate: 'ищет след',
  chase: 'преследует',
  windup: 'готовится атаковать',
  aggro: 'преследует',
  attacking: 'атакует',
  recover: 'восстанавливается',
  retreat: 'отступает',
  dead: 'повержен',
}
