export type RenderQuality = 'low' | 'medium' | 'high'

export type ProfileSettings = {
  notifications: {
    raid_alerts: boolean
    production_ready: boolean
    market_updates: boolean
  }
  render_quality: RenderQuality
}

export type PlayerProfile = {
  display_name: string
  city_name: string
  avatar_url: string
  level: number
  xp: number
  level_start_xp?: number
  next_level_xp: number | null
  settings: ProfileSettings
  updated_at: string
}

export type Player = {
  id: string
  email: string
  name: string
  status: 'active' | 'suspended' | 'deleted'
  role: 'user' | 'admin'
  profile: PlayerProfile
  created_at: string
  updated_at: string
}

export type AuthResponse = {
  player: Player
  access_token: string
  refresh_token: string
  access_until: string
  refresh_until: string
}
