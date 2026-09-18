import type { WorldTile } from '../../shared/contracts'

export function canChopForestTile(tile: WorldTile | null | undefined) {
  return tile?.terrain === 'forest' && tile.forest_density > 0
}
