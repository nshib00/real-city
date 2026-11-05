const compact = new Intl.NumberFormat('ru-RU', { notation: 'compact', maximumFractionDigits: 1 })
const ordinary = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })
const full = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })

// Точное значение остаётся в aria-label/title родительского счётчика.
export function formatAmount(amount: number) {
  return Math.abs(amount) >= 1_000_000 ? compact.format(amount) : ordinary.format(amount)
}

export function formatFullAmount(amount: number) {
  return full.format(amount)
}
