import { activeThreePreviewCount } from '../renderers/threePreviewBudget'

export type RenderPerformanceSnapshot = {
  fps: number
  frameP50Ms: number
  frameP95Ms: number
  activePixiContexts: number
  activeThreePreviews: number
  usedHeapMb: number | null
  visible: { tiles: number; buildings: number; resources: number; monsters: number }
  pixiChildren: { terrain: number; objects: number }
  retainedCaches: { terrain: number; buildings: number; resources: number; overlays: number }
  redraw: { count: number; created: number; destroyed: number }
}

const FRAME_WINDOW_MS = 1500

let activePixiContexts = 0
let frameTimes: number[] = []
let created = 0
let destroyed = 0
let stageMetrics = emptyStageMetrics()

function emptyStageMetrics() {
  return {
    visible: { tiles: 0, buildings: 0, resources: 0, monsters: 0 },
    pixiChildren: { terrain: 0, objects: 0 },
    retainedCaches: { terrain: 0, buildings: 0, resources: 0, overlays: 0 },
    redraw: { count: 0, created: 0, destroyed: 0 },
  }
}

export function registerPixiContext() {
  activePixiContexts += 1
  return () => {
    activePixiContexts = Math.max(0, activePixiContexts - 1)
    if (activePixiContexts === 0) {
      frameTimes = []
      created = 0
      destroyed = 0
      stageMetrics = emptyStageMetrics()
    }
  }
}

export function recordPixiFrame(nowMs: number) {
  frameTimes.push(nowMs)
  const cutoff = nowMs - FRAME_WINDOW_MS
  let expired = 0
  while (expired < frameTimes.length && frameTimes[expired] < cutoff) expired++
  if (expired) frameTimes.splice(0, expired)
}

export function recordPixiChildMutation(createdCount: number, destroyedCount: number) {
  if (!import.meta.env.DEV) return
  created += createdCount
  destroyed += destroyedCount
}

export function pixiMutationCounts() {
  return { created, destroyed }
}

export function recordPixiRedraw(
  metrics: Omit<ReturnType<typeof emptyStageMetrics>, 'redraw'>,
  before: { created: number; destroyed: number },
) {
  stageMetrics = {
    ...metrics,
    redraw: {
      count: stageMetrics.redraw.count + 1,
      created: created - before.created,
      destroyed: destroyed - before.destroyed,
    },
  }
}

export function renderPerformanceSnapshot(): RenderPerformanceSnapshot {
  const first = frameTimes[0]
  const last = frameTimes[frameTimes.length - 1]
  const durationSec = first !== undefined && last !== undefined ? Math.max(0.001, (last - first) / 1000) : 0
  const intervals = frameTimes.slice(1).map((time, index) => time - frameTimes[index]).sort((a, b) => a - b)
  const percentile = (fraction: number) => intervals.length > 0 ? Math.round(intervals[Math.ceil(intervals.length * fraction) - 1] * 10) / 10 : 0
  return {
    fps: frameTimes.length > 1 ? Math.round(((frameTimes.length - 1) / durationSec) * 10) / 10 : 0,
    frameP50Ms: percentile(0.5),
    frameP95Ms: percentile(0.95),
    activePixiContexts,
    activeThreePreviews: activeThreePreviewCount(),
    usedHeapMb: usedHeapMb(),
    ...stageMetrics,
  }
}

export function resetRenderPerformanceMetricsForTests() {
  activePixiContexts = 0
  frameTimes = []
  created = 0
  destroyed = 0
  stageMetrics = emptyStageMetrics()
}

function usedHeapMb() {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return null
  }
  const memory = performance.memory as { usedJSHeapSize?: number }
  return typeof memory.usedJSHeapSize === 'number' ? Math.round(memory.usedJSHeapSize / 1024 / 1024) : null
}
