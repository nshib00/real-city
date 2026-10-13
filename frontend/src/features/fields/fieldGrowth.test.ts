import { describe, expect, it } from 'vitest'

import { fieldCropSpec } from './fieldGrowth'

describe('field crop runtime specs', () => {
  it('configures every buildable field crop for click actions', () => {
    for (const type of ['field_bed', 'seed_garden', 'herb_bed', 'mushroom_grove', 'flax_field', 'reed_bed', 'dye_garden', 'oilseed_field', 'sugar_bed', 'crystal_greenhouse']) {
      const spec = fieldCropSpec(type)
      expect(spec, type).not.toBeNull()
      expect(spec?.stages, type).toBeGreaterThan(0)
      expect(spec?.rewardsByLevel.length, type).toBeGreaterThan(0)
    }
  })
})
