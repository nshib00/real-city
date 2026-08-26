export type PopulationSummary = {
  total: number
  free: number
  builders: number
  production: number
  fields: number
  defense: number
  repair: number
}

export function busyPopulation(summary: PopulationSummary) {
  return summary.builders + summary.production + summary.fields + summary.defense + summary.repair
}

