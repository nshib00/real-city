import { describe, expect, it } from 'vitest'

import { RESOURCE_ICON_ASSET_REVISION, resourceIconUrl } from './ResourceIcon'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import manifest from '../../../public/assets/resources/icons/manifest.json'

describe('resource icons', () => {
  it('uses the legacy resource set and never constructs paths from unknown ids', () => {
    expect(resourceIconUrl('wood')).toBe(`/assets/resources/icons/wood.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    expect(resourceIconUrl('aeolian-crystal')).toBe(`/assets/resources/icons/aeolian-crystal.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    expect(resourceIconUrl('kaolin')).toBe('/assets/resources/icons/kaolin.svg')
    expect(resourceIconUrl('quiet_powder')).toContain('/assets/resources/icons/silent_powder.png')
    expect(resourceIconUrl('plant_oil')).toContain('/assets/resources/icons/vegetable_oil.png')
    expect(resourceIconUrl('oleoresin')).toContain('/assets/resources/icons/sap.png')
    expect(resourceIconUrl('../unknown')).toContain('/assets/ui/icons/shortage.svg')
  })

  it('matches catalog metadata for resource icons that have been generated', () => {
    for (const item of resourceCatalog) {
      const generated = manifest.resources.find((entry) => entry.id === item.id)
      if (!generated) continue
      expect(generated).toEqual(expect.objectContaining({
        id: item.id,
        file: `${item.id}.png`,
      }))
    }
  })

  it('registers every weapon resource without changing world models', () => {
    for (const item of resourceCatalog.filter((resource) => resource.category === 'weapons')) {
      expect(manifest.resources.find((entry) => entry.id === item.id)).toEqual(expect.objectContaining({
        id: item.id,
        name: item.name,
        file: `${item.id}.png`,
      }))
      expect(resourceIconUrl(item.id)).toBe(`/assets/resources/icons/${item.id}.png?v=${RESOURCE_ICON_ASSET_REVISION}`)
    }
  })
})
