import { request } from './client'
import type { PublicPlayerProfile } from '../../../../shared/player/profile'
export function getPublicProfile(id: string) { return request<{ profile: PublicPlayerProfile }>(`/players/${encodeURIComponent(id)}/profile`) }
