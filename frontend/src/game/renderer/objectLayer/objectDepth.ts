type TileCoord = {
  x: number
  y: number
}

const OBJECT_LAYER_OFFSET = 10_000

export function objectLayerSortKey(tile: TileCoord, layerOffset = 0, footprintOffset = 0) {
  return tile.x + tile.y + OBJECT_LAYER_OFFSET + layerOffset + footprintOffset
}

