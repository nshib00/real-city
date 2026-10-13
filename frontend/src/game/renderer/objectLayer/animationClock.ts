import type { BuildingAnimationKey } from '../../renderers/assetManifestTypes'

export type AnimationFrameInput = {
  nowMs: number
  fps: number
  frames?: number
  loop: boolean
  phaseOffsetMs?: number
}

const FAR_ZOOM_THRESHOLD = 0.58
const IMPORTANT_OVERLAYS = new Set<BuildingAnimationKey>(['damaged_smoke', 'damaged_fire', 'ready_to_collect', 'under_attack'])

export function animationFrameIndex({ nowMs, fps, frames, loop, phaseOffsetMs = 0 }: AnimationFrameInput) {
  const frameCount = Math.max(0, Math.floor(frames ?? 0))
  if (frameCount === 0 || fps <= 0) {
    return 0
  }

  const frameDurationMs = 1000 / fps
  const elapsedFrames = Math.floor(Math.max(0, nowMs + phaseOffsetMs) / frameDurationMs)
  if (loop) {
    return elapsedFrames % frameCount
  }
  return Math.min(elapsedFrames, frameCount - 1)
}

export function animationPhaseOffsetMs(id: string, durationMs = 1000) {
  const duration = Math.max(1, Math.floor(durationMs))
  let hash = 2166136261
  for (let index = 0; index < id.length; index += 1) {
    hash ^= id.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return Math.abs(hash) % duration
}

export function shouldRenderBuildingOverlay(key: BuildingAnimationKey, zoom: number, selected = false) {
  if (selected || zoom >= FAR_ZOOM_THRESHOLD) {
    return true
  }
  return IMPORTANT_OVERLAYS.has(key)
}
