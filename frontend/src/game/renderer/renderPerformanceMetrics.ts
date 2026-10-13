import { activeThreePreviewCount } from '../renderers/threePreviewBudget'

export type RenderPerformanceSnapshot = {
  fps: number
  activePixiContexts: number
  activeThreePreviews: number
  usedHeapMb: number | null
}

const FRAME_WINDOW_MS = 1500

let activePixiContexts = 0
let frameTimes: number[] = []

export function registerPixiContext() {
  activePixiContexts += 1
  return () => {
    activePixiContexts = Math.max(0, activePixiContexts - 1)
  }
}

export function recordPixiFrame(nowMs: number) {
  frameTimes.push(nowMs)
  const cutoff = nowMs - FRAME_WINDOW_MS
  frameTimes = frameTimes.filter((time) => time >= cutoff)
}

export function renderPerformanceSnapshot(): RenderPerformanceSnapshot {
  const first = frameTimes[0]
  const last = frameTimes[frameTimes.length - 1]
  const durationSec = first !== undefined && last !== undefined ? Math.max(0.001, (last - first) / 1000) : 0
  return {
    fps: frameTimes.length > 1 ? Math.round(((frameTimes.length - 1) / durationSec) * 10) / 10 : 0,
    activePixiContexts,
    activeThreePreviews: activeThreePreviewCount(),
    usedHeapMb: usedHeapMb(),
  }
}

export function resetRenderPerformanceMetricsForTests() {
  activePixiContexts = 0
  frameTimes = []
}

function usedHeapMb() {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return null
  }
  const memory = performance.memory as { usedJSHeapSize?: number }
  return typeof memory.usedJSHeapSize === 'number' ? Math.round(memory.usedJSHeapSize / 1024 / 1024) : null
}
