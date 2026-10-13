import { request } from './client'
import type { BuildingResponse } from './buildings'

export type InventoryItem = {
  resource: string
  amount: number
}

export type InventoryResponse = {
  player_id: string
  items: InventoryItem[]
  coin_capacity: number
  updated_at: string
}

export type ResourceNodeResponse = {
  id: string
  type: string
  resource: string
  amount: number
  max_amount: number
  state: 'neutral' | 'claimed' | 'depleted'
  owner_id: string
  tile_x: number
  tile_y: number
  respawn_at: string | null
}

export type ProductionRecipeResponse = {
  id: string
  name: string
  building_type: string
  duration_sec: number
  workers: number
  input: InventoryItem[]
  output: InventoryItem[]
  rare_output: (InventoryItem & { chance: number })[]
}

export type ProductionJobResponse = {
  id: string
  building_id: string
  recipe_id: string
  state: 'running' | 'ready' | 'completed' | 'cancelled'
  started_at: string
  completes_at: string
}

export function getInventory() {
  return request<{ inventory: InventoryResponse }>('/economy/inventory')
}

export function listResourceNodes() {
  return request<{ nodes: ResourceNodeResponse[] }>('/resources/nodes')
}

export function patchResourceNode(id: string, action: 'claim' | 'harvest') {
  return request<{ node: ResourceNodeResponse; inventory?: InventoryResponse }>(`/resources/nodes/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action }),
  })
}

export function listProductionRecipes() {
  return request<{ recipes: ProductionRecipeResponse[] }>('/production/recipes')
}

export function listProductionJobs() {
  return request<{ jobs: ProductionJobResponse[] }>('/production/jobs')
}

export function startProduction(input: { building_id: string; recipe_id: string }) {
  return request<{ job: ProductionJobResponse; inventory: InventoryResponse }>('/production/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function patchProductionJob(id: string, action: 'complete' | 'cancel') {
  return request<{ job: ProductionJobResponse; inventory?: InventoryResponse }>(`/production/jobs/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action }),
  })
}

export function advanceWindleafField(buildingId: string) {
  return request<{ building: BuildingResponse; inventory: InventoryResponse }>('/fields/windleaf/advance', {
    method: 'POST',
    body: JSON.stringify({ building_id: buildingId }),
  })
}

export function harvestWindleafField(buildingId: string) {
  return request<{ building: BuildingResponse; inventory: InventoryResponse }>('/fields/windleaf/harvest', {
    method: 'POST',
    body: JSON.stringify({ building_id: buildingId }),
  })
}

export function advanceField(buildingId: string) {
  return request<{ building: BuildingResponse; inventory: InventoryResponse }>('/fields/advance', {
    method: 'POST',
    body: JSON.stringify({ building_id: buildingId }),
  })
}

export function harvestField(buildingId: string) {
  return request<{ building: BuildingResponse; inventory: InventoryResponse }>('/fields/harvest', {
    method: 'POST',
    body: JSON.stringify({ building_id: buildingId }),
  })
}
