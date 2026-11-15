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
  redraw: {
    count: number
    created: number
    destroyed: number
    samples10s: number
    phases: Record<RedrawPhase, { p50Ms: number; p95Ms: number }>
    objects: { buildings: number; resources: number; monsters: number; buildingCommands: number; resourceCommands: number; overlayCommands: number }
  }
  animation: {
    monsters: { samples10s: number; p50Ms: number; p95Ms: number; items: number }
    buildingOverlays: { samples10s: number; p50Ms: number; p95Ms: number; items: number }
  }
}

const FRAME_WINDOW_MS = 1500
const DIAGNOSTIC_WINDOW_MS = 10_000

export type RedrawPhase = 'terrain' | 'mapOverlays' | 'commandBuild' | 'buildings' | 'resources' | 'monsters' | 'buildingOverlays' | 'total'
export type RedrawDiagnostics = {
  phases: Record<RedrawPhase, number>
  objects: RenderPerformanceSnapshot['redraw']['objects']
}
export type AnimationDiagnosticKind = 'monsters' | 'buildingOverlays'

let activePixiContexts = 0
let frameTimes: number[] = []
let created = 0
let destroyed = 0
let stageMetrics = emptyStageMetrics()
let redrawSamples: Array<{ at: number; phases: Record<RedrawPhase, number>; objects: RedrawDiagnostics['objects'] }> = []
let animationSamples: Record<AnimationDiagnosticKind, Array<{ at: number; durationMs: number; items: number }>> = {
  monsters: [],
  buildingOverlays: [],
}

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
      redrawSamples = []
      animationSamples = { monsters: [], buildingOverlays: [] }
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
  diagnostics: RedrawDiagnostics,
) {
  if (!import.meta.env.DEV) return
  const at = performance.now()
  redrawSamples.push({ at, phases: diagnostics.phases, objects: diagnostics.objects })
  pruneSamples(redrawSamples, at)
  stageMetrics = {
    ...metrics,
    redraw: {
      count: stageMetrics.redraw.count + 1,
      created: created - before.created,
      destroyed: destroyed - before.destroyed,
    },
  }
}

export function recordPixiAnimation(kind: AnimationDiagnosticKind, durationMs: number, items: number, at = performance.now()) {
  if (!import.meta.env.DEV) return
  const samples = animationSamples[kind]
  samples.push({ at, durationMs, items })
  pruneSamples(samples, at)
}

export function renderPerformanceSnapshot(): RenderPerformanceSnapshot {
  const first = frameTimes[0]
  const last = frameTimes[frameTimes.length - 1]
  const durationSec = first !== undefined && last !== undefined ? Math.max(0.001, (last - first) / 1000) : 0
  const intervals = frameTimes.slice(1).map((time, index) => time - frameTimes[index]).sort((a, b) => a - b)
  const percentile = (values: number[], fraction: number) => values.length > 0 ? Math.round(values[Math.ceil(values.length * fraction) - 1] * 10) / 10 : 0
  const phaseValues = (phase: RedrawPhase) => redrawSamples.map((sample) => sample.phases[phase]).sort((a, b) => a - b)
  const animationSummary = (kind: AnimationDiagnosticKind) => {
    const samples = animationSamples[kind]
    const values = samples.map((sample) => sample.durationMs).sort((a, b) => a - b)
    return {
      samples10s: samples.length,
      p50Ms: percentile(values, 0.5),
      p95Ms: percentile(values, 0.95),
      items: samples.at(-1)?.items ?? 0,
    }
  }
  return {
    fps: frameTimes.length > 1 ? Math.round(((frameTimes.length - 1) / durationSec) * 10) / 10 : 0,
    frameP50Ms: percentile(intervals, 0.5),
    frameP95Ms: percentile(intervals, 0.95),
    activePixiContexts,
    activeThreePreviews: activeThreePreviewCount(),
    usedHeapMb: usedHeapMb(),
    visible: stageMetrics.visible,
    pixiChildren: stageMetrics.pixiChildren,
    retainedCaches: stageMetrics.retainedCaches,
    redraw: {
      ...stageMetrics.redraw,
      samples10s: redrawSamples.length,
      phases: Object.fromEntries(REDRAW_PHASES.map((phase) => {
        const values = phaseValues(phase)
        return [phase, { p50Ms: percentile(values, 0.5), p95Ms: percentile(values, 0.95) }]
      })) as Record<RedrawPhase, { p50Ms: number; p95Ms: number }>,
      objects: redrawSamples.at(-1)?.objects ?? { buildings: 0, resources: 0, monsters: 0, buildingCommands: 0, resourceCommands: 0, overlayCommands: 0 },
    },
    animation: {
      monsters: animationSummary('monsters'),
      buildingOverlays: animationSummary('buildingOverlays'),
    },
  }
}

const REDRAW_PHASES: RedrawPhase[] = ['terrain', 'mapOverlays', 'commandBuild', 'buildings', 'resources', 'monsters', 'buildingOverlays', 'total']

function pruneSamples<T extends { at: number }>(samples: T[], now: number) {
  const cutoff = now - DIAGNOSTIC_WINDOW_MS
  let expired = 0
  while (expired < samples.length && samples[expired].at < cutoff) expired++
  if (expired) samples.splice(0, expired)
}

export function resetRenderPerformanceMetricsForTests() {
  activePixiContexts = 0
  frameTimes = []
  created = 0
  destroyed = 0
  stageMetrics = emptyStageMetrics()
  redrawSamples = []
  animationSamples = { monsters: [], buildingOverlays: [] }
}

function usedHeapMb() {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return null
  }
  const memory = performance.memory as { usedJSHeapSize?: number }
  return typeof memory.usedJSHeapSize === 'number' ? Math.round(memory.usedJSHeapSize / 1024 / 1024) : null
}
