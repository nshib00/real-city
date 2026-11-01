import { request } from './client'
import { normalizeTile } from '../../../../shared/world/coordinates'

export type NearbyPlayer = {
  player_id: string
  name: string
  level: number
  tile_x: number
  tile_y: number
}

export function updatePlayerPresence(tile: { x: number; y: number }) {
  tile = normalizeTile(tile)
  return request<{ status: string }>('/players/me/presence', {
    method: 'POST',
    body: JSON.stringify({ tile_x: tile.x, tile_y: tile.y }),
  })
}

export function listNearbyPlayers(center: { x: number; y: number }, radius: number) {
  center = normalizeTile(center)
  return request<{ players: NearbyPlayer[] }>(`/players/nearby?x=${center.x}&y=${center.y}&radius=${radius}`)
}
