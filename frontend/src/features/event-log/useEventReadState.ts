import { useEffect, useState } from 'react'

function load(key: string): string[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key) ?? '[]')
    return Array.isArray(value) ? value.filter((id): id is string => typeof id === 'string').slice(-200) : []
  } catch { return [] }
}

export function useEventReadState(playerId: string | undefined, ids: string[], visible: boolean) {
  const key = `real-city.events.read.${playerId ?? 'anonymous'}`
  const [state, setState] = useState(() => ({ key, ids: load(key) }))
  const readIds = state.key === key ? state.ids : load(key)
  const unread = new Set(ids.filter((id) => !readIds.includes(id))).size
  // IDs are stable across repeated WS frames. Never acknowledge a hidden tab.
  const signature = JSON.stringify(ids)
  useEffect(() => {
    const mark = () => {
      if (!playerId || !visible || document.hidden) return
      setState((previous) => {
        const current = previous.key === key ? previous.ids : load(key)
        const next = [...new Set([...current, ...JSON.parse(signature) as string[]])].slice(-200)
        try { localStorage.setItem(key, JSON.stringify(next)) } catch { /* session still works without storage */ }
        return { key, ids: next }
      })
    }
    mark()
    document.addEventListener('visibilitychange', mark)
    return () => document.removeEventListener('visibilitychange', mark)
  }, [key, playerId, signature, visible])
  return unread
}
