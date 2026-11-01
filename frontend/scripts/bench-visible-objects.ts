import { performance } from 'node:perf_hooks'
import { filterVisibleIndexedMapObjects, filterVisibleMapObjects, indexMapObjects } from '../src/game/renderer/visibleObjects'
import { wrappedGridDistance } from '../src/game/coordinates/iso'
import { indexWorldTiles, worldTilesNear } from '../src/game/renderer/worldTileIndex'
import type { WorldTile } from '../src/shared/contracts'

const objects = Array.from({ length: 10_000 }, (_, id) => ({
  id,
  tile: { x: (id * 7919) % 160, y: (Math.floor(id * 0.61803398875) * 1223) % 160 },
}))
const cameras = Array.from({ length: 200 }, (_, id) => ({
  camera: { x: -id * 31, y: id * 17, zoom: 0.8 + (id % 5) * 0.2 },
  viewportSize: { width: 1280, height: 800 },
}))
const indexStarted = performance.now()
const index = indexMapObjects(objects)
const indexMs = performance.now() - indexStarted

function measure(filter: (options: typeof cameras[number]) => typeof objects) {
  const runs = []
  for (let run = 0; run < 6; run += 1) {
    const started = performance.now()
    let visible = 0
    for (const options of cameras) visible += filter(options).length
    if (run > 0) runs.push(performance.now() - started)
    if (run === 0) console.log(`Видимых объектов за 200 положений камеры: ${visible}`)
  }
  return runs.sort((a, b) => a - b)[Math.floor(runs.length / 2)]
}

const linearMs = measure((options) => filterVisibleMapObjects(objects, options))
const indexedMs = measure((options) => filterVisibleIndexedMapObjects(index, options))
console.log(JSON.stringify({ objects: objects.length, cameraPositions: cameras.length, indexMs: Number(indexMs.toFixed(2)), linearMedianMs: Number(linearMs.toFixed(2)), indexedMedianMs: Number(indexedMs.toFixed(2)) }))

const tiles = Array.from({ length: 96 * 96 }, (_, id) => ({ x: id % 96, y: Math.floor(id / 96) }) as WorldTile)
const tileIndex = indexWorldTiles(tiles)
const centers = Array.from({ length: 200 }, (_, id) => ({ x: id * 0.8, y: id * 1.3 }))
function measureTiles(indexed: boolean) {
  const runs = []
  for (let run = 0; run < 6; run += 1) {
    const started = performance.now()
    let visible = 0
    for (const center of centers) {
      const candidates = indexed ? worldTilesNear(tileIndex, center, 15) : tiles
      visible += candidates.filter((tile) => wrappedGridDistance(tile.x, center.x) <= 15 && wrappedGridDistance(tile.y, center.y) <= 15).length
    }
    if (run > 0) runs.push(performance.now() - started)
    if (run === 0) console.log(`Тайлов в радиусе за 200 положений камеры: ${visible}`)
  }
  return runs.sort((a, b) => a - b)[Math.floor(runs.length / 2)]
}
console.log(JSON.stringify({ tiles: tiles.length, cameraPositions: centers.length, tileLinearMedianMs: Number(measureTiles(false).toFixed(2)), tileIndexedMedianMs: Number(measureTiles(true).toFixed(2)) }))
