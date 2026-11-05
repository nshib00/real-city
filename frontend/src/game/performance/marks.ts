const startedAt = new Map<string, number>()

export function beginMapMeasure(name: string) {
  if (typeof performance === 'undefined') return
  startedAt.set(name, performance.now())
  performance.mark(`real-city:${name}:start`)
}

export function endMapMeasure(name: string) {
  if (typeof performance === 'undefined') return
  const start = startedAt.get(name)
  if (start === undefined) return
  startedAt.delete(name)
  performance.mark(`real-city:${name}:end`)
  performance.measure(`real-city:${name}`, `real-city:${name}:start`, `real-city:${name}:end`)
  if (import.meta.env.DEV && performance.now() - start > 1000) {
    console.warn(`real-city performance: ${name} took ${Math.round(performance.now() - start)} ms`)
  }
}
