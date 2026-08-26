import type { ResourceNode } from '../state/useGameStore'

export function resourceNodeClassName(node: ResourceNode) {
  return `map-resource-node map-resource-node-${node.resource} map-resource-node-${node.state}`
}

export function resourceNodeLabel(node: ResourceNode) {
  const labels: Record<string, string> = {
    wood: 'Древесина',
    stone: 'Камень',
    oil: 'Нефтяная скважина',
  }
  return `${labels[node.resource] ?? node.resource}: ${node.amount}/${node.maxAmount}`
}

export function resourceNodeRenderState(node: ResourceNode) {
  if (node.state === 'depleted') {
    return 'depleted'
  }
  if (node.ownerId) {
    return 'claimed'
  }
  return 'neutral'
}

