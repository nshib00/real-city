import { describe, expect, it } from 'vitest'

import { productionFormatSeconds } from './ProductionPanel'

describe('production panel helpers', () => {
  it('formats recipe duration', () => {
    expect(productionFormatSeconds(360)).toBe('6 мин.')
  })
})

