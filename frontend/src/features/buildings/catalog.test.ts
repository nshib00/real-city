import { describe, expect, it } from 'vitest'

import { buildingCatalog } from '../../../../shared/catalog/buildings'
import { registeredBuildingAssetFamilies } from '../../game/renderers/buildingRegistry'
import { buildCatalog } from './catalog'

describe('build catalog availability', () => {
  it('shows every directly buildable type and no upgrade-only type', () => {
    expect(new Set(buildCatalog.map((item) => item.kind))).toEqual(
      new Set(buildingCatalog.filter((item) => item.firstLevel).map((item) => item.type)),
    )
    expect(buildCatalog.map((item) => item.kind)).not.toContain('warehouse')
    expect(buildCatalog.some((item) => item.kind === 'stone_wall')).toBe(true)
    expect(buildCatalog.some((item) => item.kind === 'concrete_wall')).toBe(true)
    expect(buildCatalog.some((item) => item.kind === 'modern_wall')).toBe(true)
  })

  it('shows model previews for every directly buildable registered asset family', () => {
    const registeredKinds = new Set(registeredBuildingAssetFamilies().map((manifest) => manifest.kind))
    for (const item of buildCatalog.filter((entry) => registeredKinds.has(entry.kind))) {
      expect(item.previewImage, item.kind).toContain('/assets/buildings/')
    }
    for (const kind of ['paper_workshop', 'tile_factory', 'military_factory']) {
      expect(buildCatalog.find((item) => item.kind === kind)?.previewImage).toContain(`/${kind}_l01_active.png`)
    }
  })
})
