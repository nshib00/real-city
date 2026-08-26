export type PresenceState = {
  playerId: string
  online: boolean
}

export function upsertPresence(items: PresenceState[], next: PresenceState) {
  return [...items.filter((item) => item.playerId !== next.playerId), next]
}
