import { describe, expect, it } from 'vitest'

import { RESOURCE_ICON_ASSET_REVISION, resourceIconUrl } from './ResourceIcon'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import manifest from '../../../public/assets/resources/icons/manifest.json'

describe('resource icons', () => {
  it('uses generated png assets from the public resource icon folder', () => {
    expect(resourceIconUrl('wood')).toBe(`/assets/resources/icons/wood.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    expect(resourceIconUrl('aeolian-crystal')).toBe(`/assets/resources/icons/aeolian-crystal.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
  })

  it('matches catalog metadata for resource icons that have been generated', () => {
    for (const item of resourceCatalog) {
      const generated = manifest.resources.find((entry) => entry.id === item.id)
      if (!generated) continue
      expect(generated).toEqual(expect.objectContaining({
        id: item.id,
        file: `${item.id}.png`,
        model: `${item.id}.glb`,
      }))
    }
  })

  it('registers a generated icon and model for every weapon resource', () => {
    for (const item of resourceCatalog.filter((resource) => resource.category === 'weapons')) {
      expect(manifest.resources.find((entry) => entry.id === item.id)).toEqual(expect.objectContaining({
        id: item.id,
        name: item.name,
        category: 'weapons',
        file: `${item.id}.png`,
        model: `${item.id}.glb`,
      }))
      expect(resourceIconUrl(item.id)).toBe(`/assets/resources/icons/${item.id}.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    }
  })
})
