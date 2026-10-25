import { screenToGrid } from '../../coordinates/iso'

type TileCoord = {
  x: number
  y: number
}

const OBJECT_LAYER_OFFSET = 10_000
const DIAGONAL_STRIDE = 1_024

export function objectLayerSortKey(tile: TileCoord, layerOffset = 0, footprintOffset = 0) {
  return (tile.x + tile.y) * DIAGONAL_STRIDE + tile.x + OBJECT_LAYER_OFFSET + layerOffset + footprintOffset
}

export function projectedObjectSortKey(position: TileCoord, layerOffset = 0, footprintOffset = 0) {
  return objectLayerSortKey(screenToGrid(position), layerOffset, footprintOffset)
}
