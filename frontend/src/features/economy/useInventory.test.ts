import { describe, expect, it } from 'vitest'

import { inventoryAmount } from './useInventory'

describe('inventory helpers', () => {
  it('returns resource amount without applying material limits', () => {
    expect(inventoryAmount([{ resource: 'wood', amount: 12000 }], 'wood')).toBe(12000)
    expect(inventoryAmount([{ resource: 'coins', amount: 2000 }], 'stone')).toBe(0)
  })
})

