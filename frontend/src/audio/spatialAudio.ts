import { CHUNK_SIZE, gridToScreen, nearestWrappedScreenCoord, type GridCoord } from '../game/coordinates/iso'

export type SpatialResult = { gain: number; pan: number }

export function spatialSound(tile: GridCoord | undefined, center: GridCoord, radiusChunks: number, zoom = 1): SpatialResult {
  if (!tile) return { gain: 0, pan: 0 }
  const centerScreen = gridToScreen(center)
  const target = nearestWrappedScreenCoord(tile, centerScreen)
  const dx = (target.x - centerScreen.x) * zoom
  const dy = (target.y - centerScreen.y) * zoom
  const radius = (radiusChunks + 1) * CHUNK_SIZE * 150
  const distance = Math.hypot(dx, dy)
  if (distance > radius) return { gain: 0, pan: 0 }
  return { gain: Math.max(0.12, 1 - distance / radius), pan: Math.max(-0.85, Math.min(0.85, dx / (radius * 0.55))) }
}
