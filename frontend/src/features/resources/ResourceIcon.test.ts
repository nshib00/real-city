import { describe, expect, it } from 'vitest'

import { RESOURCE_ICON_ASSET_REVISION, resourceIconUrl } from './ResourceIcon'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import manifest from '../../../public/assets/resources/icons/manifest.json'

describe('resource icons', () => {
  it('uses generated png assets from the public resource icon folder', () => {
    expect(resourceIconUrl('wood')).toBe(`/assets/resources/icons/wood.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    expect(resourceIconUrl('aeolian-crystal')).toBe(`/assets/resources/icons/aeolian-crystal.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
  })

  it('includes an icon for every catalog resource', () => {
    expect(manifest.resources.map((item) => item.id)).toEqual(expect.arrayContaining(resourceCatalog.map((item) => item.id)))
    for (const item of resourceCatalog) {
      expect(manifest.resources.find((entry) => entry.id === item.id)).toEqual(expect.objectContaining({
        id: item.id,
        name: item.name,
        category: item.category,
        file: `${item.id}.png`,
        model: `${item.id}.glb`,
      }))
    }
  })
})
