import { request } from './client'

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
}

export type ProductionJobResponse = {
  id: string
  building_id: string
  recipe_id: string
  state: 'running' | 'completed' | 'cancelled'
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

export function harvestWindleafField(superCrop = false) {
  return request<{ inventory: InventoryResponse }>('/fields/windleaf/harvest', {
    method: 'POST',
    body: JSON.stringify({ super: superCrop }),
  })
}
