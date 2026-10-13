import { describe, expect, it } from 'vitest'

import type { ResourceNode } from '../../state/useGameStore'
import { resourceDrawCommands, resourceOverlayState } from './resourceDrawData'

describe('resource draw data', () => {
  it('turns resource nodes into sorted Pixi draw commands', () => {
    const commands = resourceDrawCommands([
      resourceNode({ id: 'stone-2', resource: 'stone', tile: { x: 5, y: 5 } }),
      resourceNode({ id: 'wood-1', resource: 'wood', tile: { x: 1, y: 1 }, amount: 25, maxAmount: 100 }),
    ])

    expect(commands.map((command) => command.id)).toEqual(['wood-1', 'stone-2'])
    expect(commands[0]).toMatchObject({
      label: 'Древесина: 25/100',
      resource: 'wood',
      amountRatio: 0.25,
      overlayState: 'neutral',
      anchor: { x: 0.5, y: 0.72 },
      size: { width: 86, height: 66 },
    })
  })

  it('derives claimed, contested and depleted overlay states', () => {
    expect(resourceOverlayState(resourceNode({ state: 'claimed', ownerId: 'player-1' }))).toBe('claimed')
    expect(resourceOverlayState(resourceNode({ state: 'claimed', ownerId: '' }))).toBe('contested')
    expect(resourceOverlayState(resourceNode({ state: 'depleted', ownerId: 'player-1' }))).toBe('depleted')
  })
})

function resourceNode(overrides: Partial<ResourceNode>): ResourceNode {
  return {
    id: 'node-1',
    type: 'deposit',
    resource: 'wood',
    amount: 50,
    maxAmount: 100,
    state: 'neutral',
    ownerId: '',
    tile: { x: 0, y: 0 },
    respawnAt: null,
    ...overrides,
  }
}
