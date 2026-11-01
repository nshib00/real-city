import { CHUNK_SIZE, nearestWrappedScreenCoord, screenToGrid, WORLD_WRAP_TILES } from '../coordinates/iso'

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
  viewportSize: ViewportSize
  margin?: number
  maxScreenExtent?: number
}

type IndexedObject<T> = { object: T; index: number }
export type MapObjectSpatialIndex<T extends MapObjectLike> = {
  objects: T[]
  buckets: Map<string, IndexedObject<T>[]>
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

export function indexMapObjects<T extends MapObjectLike>(objects: T[]): MapObjectSpatialIndex<T> {
  const buckets = new Map<string, IndexedObject<T>[]>()
  objects.forEach((object, index) => {
    const key = bucketKey(Math.floor(wrap(object.tile.x) / CHUNK_SIZE), Math.floor(wrap(object.tile.y) / CHUNK_SIZE))
    const bucket = buckets.get(key) ?? []
    bucket.push({ object, index })
    buckets.set(key, bucket)
  })
  return { objects, buckets }
}

export function filterVisibleIndexedMapObjects<T extends MapObjectLike>(index: MapObjectSpatialIndex<T>, options: VisibilityOptions) {
  const { camera, viewportSize, margin = DEFAULT_VISIBILITY_MARGIN, maxScreenExtent = MAX_MAP_OBJECT_SCREEN_EXTENT } = options
  if (viewportSize.width <= 0 || viewportSize.height <= 0 || camera.zoom <= 0) return index.objects

  const originX = viewportSize.width * 0.48 + camera.x
  const originY = viewportSize.height * 0.16 + camera.y
  const extent = Math.max(margin, maxScreenExtent * camera.zoom)
  const left = (-extent - originX) / camera.zoom
  const right = (viewportSize.width + extent - originX) / camera.zoom
  const top = (-extent - originY) / camera.zoom + 30
  const bottom = (viewportSize.height + extent - originY) / camera.zoom + 30
  const corners = [screenToGrid({ x: left, y: top }), screenToGrid({ x: right, y: top }), screenToGrid({ x: left, y: bottom }), screenToGrid({ x: right, y: bottom })]
  const minX = Math.floor(Math.min(...corners.map((corner) => corner.x)))
  const maxX = Math.ceil(Math.max(...corners.map((corner) => corner.x)))
  const minY = Math.floor(Math.min(...corners.map((corner) => corner.y)))
  const maxY = Math.ceil(Math.max(...corners.map((corner) => corner.y)))
  if (maxX - minX >= WORLD_WRAP_TILES || maxY - minY >= WORLD_WRAP_TILES) {
    return filterVisibleMapObjects(index.objects, options)
  }

  const bucketsPerAxis = WORLD_WRAP_TILES / CHUNK_SIZE
  const candidates: IndexedObject<T>[] = []
  const seenBuckets = new Set<string>()
  for (let y = Math.floor(minY / CHUNK_SIZE); y <= Math.floor(maxY / CHUNK_SIZE); y += 1) {
    for (let x = Math.floor(minX / CHUNK_SIZE); x <= Math.floor(maxX / CHUNK_SIZE); x += 1) {
      const key = bucketKey(wrap(x, bucketsPerAxis), wrap(y, bucketsPerAxis))
      if (seenBuckets.has(key)) continue
      seenBuckets.add(key)
      candidates.push(...(index.buckets.get(key) ?? []))
    }
  }
  candidates.sort((left, right) => left.index - right.index)
  return candidates.filter(({ object }) => isMapObjectVisible(object.tile, options)).map(({ object }) => object)
}

function wrap(value: number, size = WORLD_WRAP_TILES) {
  return ((value % size) + size) % size
}

function bucketKey(x: number, y: number) {
  return `${x}:${y}`
}

export function isMapObjectVisible(tile: TileCoord, options: VisibilityOptions) {
  const { camera, viewportSize, margin = DEFAULT_VISIBILITY_MARGIN, maxScreenExtent = MAX_MAP_OBJECT_SCREEN_EXTENT } = options
  if (viewportSize.width <= 0 || viewportSize.height <= 0) {
    return true
  }

  const origin = {
    x: viewportSize.width * 0.48 + camera.x,
    y: viewportSize.height * 0.16 + camera.y,
  }
  const screenTarget = {
    x: (viewportSize.width / 2 - origin.x) / camera.zoom,
    y: (viewportSize.height / 2 - origin.y) / camera.zoom,
  }
  const pos = nearestWrappedScreenCoord(tile, screenTarget)
  const x = origin.x + pos.x * camera.zoom
  const y = origin.y + (pos.y - 30) * camera.zoom
  const effectiveMargin = Math.max(margin, maxScreenExtent * camera.zoom)

  return x >= -effectiveMargin
    && x <= viewportSize.width + effectiveMargin
    && y >= -effectiveMargin
    && y <= viewportSize.height + effectiveMargin
}
