export type TileCoord = {
  x: number
  y: number
}

// Terrain is drawn at its nearest wrapped screen position. Resolve clicks back
// to the coordinates of the tile that was actually loaded from the server.
export function createRenderedTileLookup<TTile extends TileCoord>(tiles: readonly TTile[], worldSize: number) {
  const wrapped = new Map<string, TTile>()
  for (const tile of tiles) {
    const key = `${modulo(tile.x, worldSize)}:${modulo(tile.y, worldSize)}`
    if (!wrapped.has(key) || (tile.x >= 0 && tile.x < worldSize && tile.y >= 0 && tile.y < worldSize)) wrapped.set(key, tile)
  }
  return (coord: TileCoord): TTile | null => wrapped.get(`${modulo(coord.x, worldSize)}:${modulo(coord.y, worldSize)}`) ?? null
}

function modulo(value: number, divisor: number) {
  return ((value % divisor) + divisor) % divisor
}

export type BuildingTileHit<TBuilding extends { tile: TileCoord }> = {
  building: TBuilding
  sortKey: number
}

export function buildingHitAtTile<TBuilding extends { tile: TileCoord }>(
  tile: TileCoord | null,
  areas: readonly BuildingTileHit<TBuilding>[],
) {
  if (!tile) {
    return null
  }
  const matches = areas
    .filter((area) => area.building.tile.x === tile.x && area.building.tile.y === tile.y)
    .sort((left, right) => right.sortKey - left.sortKey)
  return matches[0]?.building ?? null
}

export function buildingHitAtClick<TBuilding extends { tile: TileCoord }>(
  tile: TileCoord | null,
  areas: readonly BuildingTileHit<TBuilding>[],
  buildingAtPoint: TBuilding | null,
) {
  return buildingHitAtTile(tile, areas) ?? buildingAtPoint
}
