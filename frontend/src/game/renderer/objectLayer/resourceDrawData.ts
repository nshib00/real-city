import type { ResourceNode } from '../../state/useGameStore'
import { resourceNodeLabel, resourceNodeRenderState } from '../../renderers/resources'
import { objectLayerSortKey } from './objectDepth'

type TileCoord = {
  x: number
  y: number
}

export type ResourceOverlayState = 'neutral' | 'claimed' | 'contested' | 'depleted'

export type ResourceDrawCommand = {
  id: string
  node: ResourceNode
  label: string
  tile: TileCoord
  resource: string
  amountRatio: number
  overlayState: ResourceOverlayState
  anchor: { x: number; y: number }
  size: { width: number; height: number }
  sortKey: number
}

const DEFAULT_RESOURCE_SPRITE = {
  width: 86,
  height: 66,
  anchorX: 0.5,
  anchorY: 0.72,
}

export function resourceDrawCommands(nodes: readonly ResourceNode[]): ResourceDrawCommand[] {
  return nodes
	.filter((node) => node.resource !== 'oil' || node.state !== 'depleted')
    .map(resourceDrawCommand)
    .sort((left, right) => left.sortKey - right.sortKey || left.id.localeCompare(right.id))
}

export function resourceDrawCommand(node: ResourceNode): ResourceDrawCommand {
  return {
    id: node.id,
    node,
    label: resourceNodeLabel(node),
    tile: node.tile,
    resource: node.resource,
    amountRatio: resourceAmountRatio(node),
    overlayState: resourceOverlayState(node),
    anchor: { x: DEFAULT_RESOURCE_SPRITE.anchorX, y: DEFAULT_RESOURCE_SPRITE.anchorY },
    size: { width: DEFAULT_RESOURCE_SPRITE.width, height: DEFAULT_RESOURCE_SPRITE.height },
    sortKey: objectLayerSortKey(node.tile, 0.18),
  }
}

export function resourceOverlayState(node: ResourceNode): ResourceOverlayState {
  if (node.state === 'depleted') {
    return 'depleted'
  }
  if (node.state === 'claimed' && !node.ownerId) {
    return 'contested'
  }
  return resourceNodeRenderState(node)
}

function resourceAmountRatio(node: ResourceNode) {
  if (node.maxAmount <= 0) {
    return 0
  }
  return Math.max(0, Math.min(1, node.amount / node.maxAmount))
}
