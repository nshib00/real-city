import { describe, expect, it } from 'vitest'

import { resourceNodeClassName, resourceNodeRenderState } from './resources'
import type { ResourceNode } from '../state/useGameStore'

const baseNode: ResourceNode = {
  id: 'node_oil_1',
  type: 'oil_well',
  resource: 'oil',
  amount: 12,
  maxAmount: 36,
  state: 'neutral',
  ownerId: '',
  tile: { x: 1, y: 2 },
  respawnAt: null,
}

describe('resource node renderer', () => {
  it('marks oil wells and state in css class', () => {
    expect(resourceNodeClassName(baseNode)).toContain('map-resource-node-oil')
    expect(resourceNodeClassName({ ...baseNode, state: 'depleted' })).toContain('map-resource-node-depleted')
  })

  it('derives claimed render state from owner', () => {
    expect(resourceNodeRenderState({ ...baseNode, ownerId: 'p1' })).toBe('claimed')
  })
})

