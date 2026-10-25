export function formatRemaining(ms: number): string {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const seconds = totalSeconds % 60
  const minutes = Math.floor(totalSeconds / 60) % 60
  const hours = Math.floor(totalSeconds / 3600) % 24
  const days = Math.floor(totalSeconds / 86400)
  const twoDigits = (value: number) => String(value).padStart(2, '0')

  if (days > 0) {
    return `${twoDigits(days)}:${twoDigits(hours)}:${twoDigits(minutes)}:${twoDigits(seconds)}`
  }
  if (totalSeconds >= 3600) {
    return `${twoDigits(hours)}:${twoDigits(minutes)}:${twoDigits(seconds)}`
  }
  return `${twoDigits(minutes)}:${twoDigits(seconds)}`
}
