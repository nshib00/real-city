import { Box3, BoxGeometry, Group, Mesh, Vector3 } from 'three'
import { describe, expect, it } from 'vitest'

import { fitModelToCell } from './BuildingGlbModel'

describe('BuildingGlbModel', () => {
  it('centers a Y-up GLB and scales its ground footprint, not its height', () => {
    const model = new Group()
    const mesh = new Mesh(new BoxGeometry(2, 8, 4))
    mesh.position.set(5, 3, -4)
    model.add(mesh)

    fitModelToCell(model, Box3, Vector3)

    const bounds = new Box3().setFromObject(model)
    const center = bounds.getCenter(new Vector3())
    const size = bounds.getSize(new Vector3())
    expect(center.length()).toBeCloseTo(0)
    expect(Math.max(size.x, size.z)).toBeCloseTo(3.55)
    expect(size.y).toBeGreaterThan(size.z)

    mesh.geometry.dispose()
  })
})
