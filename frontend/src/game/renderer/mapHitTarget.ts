export type TileCoord = {
  x: number
  y: number
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
