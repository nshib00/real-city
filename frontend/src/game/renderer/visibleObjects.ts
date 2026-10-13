import { gridToScreen, nearestWrappedScreenCoord } from '../coordinates/iso'

type TileCoord = {
  x: number
  y: number
}

type Camera = {
  x: number
  y: number
  zoom: number
}

type ViewportSize = {
  width: number
  height: number
}

type MapObjectLike = {
  tile: TileCoord
}

type VisibilityOptions = {
  camera: Camera
  viewportCenter: TileCoord
  viewportSize: ViewportSize
  margin?: number
}

const DEFAULT_VISIBILITY_MARGIN = 320
const MAX_MAP_OBJECT_SCREEN_EXTENT = 720

export function tileOccupancyKey(tile: TileCoord) {
  return `${tile.x}:${tile.y}`
}

export function occupiedTileKeys(objects: MapObjectLike[]) {
  return new Set(objects.map((object) => tileOccupancyKey(object.tile)))
}

export function filterVisibleMapObjects<T extends MapObjectLike>(objects: T[], options: VisibilityOptions) {
  const { viewportSize } = options
  if (viewportSize.width <= 0 || viewportSize.height <= 0) {
    return objects
  }

  return objects.filter((object) => isMapObjectVisible(object.tile, options))
}

export function isMapObjectVisible(tile: TileCoord, options: VisibilityOptions) {
  const { camera, viewportCenter, viewportSize, margin = DEFAULT_VISIBILITY_MARGIN } = options
  if (viewportSize.width <= 0 || viewportSize.height <= 0) {
    return true
  }

  const origin = {
    x: viewportSize.width * 0.48 + camera.x,
    y: viewportSize.height * 0.16 + camera.y,
  }
  const screenTarget = gridToScreen(viewportCenter)
  const pos = nearestWrappedScreenCoord(tile, screenTarget)
  const x = origin.x + pos.x * camera.zoom
  const y = origin.y + (pos.y - 30) * camera.zoom
  const effectiveMargin = Math.max(margin, MAX_MAP_OBJECT_SCREEN_EXTENT * camera.zoom)

  return x >= -effectiveMargin
    && x <= viewportSize.width + effectiveMargin
    && y >= -effectiveMargin
    && y <= viewportSize.height + effectiveMargin
}
