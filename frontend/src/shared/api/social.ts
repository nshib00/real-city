import { request } from './client'

export type AllianceRole = 'leader' | 'deputy' | 'officer' | 'member'

export type AllianceProfile = {
  alliance: Alliance | null
  self: AllianceMember | null
  members: AllianceMember[]
  invites: AllianceInvite[]
  treasury: TreasuryEntry[]
  balance?: Record<string, number>
  buffs: AllianceBuff[]
  aid: TerritoryAid[]
}

export type Alliance = {
  id: string
  name: string
  leader_id: string
  level: number
  member_limit: number
}

export type AllianceMember = {
  player_id: string
  role: AllianceRole
  treasurer: boolean
  joined_at: string
}

export type AllianceInvite = {
  id: string
  alliance_id: string
  inviter_id: string
  invitee_id: string
  status: 'pending' | 'accepted' | 'declined'
  created_at: string
}

export type TreasuryEntry = {
  id: string
  player_id: string
  kind: 'donation' | 'spend'
  resource: string
  amount: number
  created_at: string
}

export type AllianceBuff = {
  id: string
  level: number
}

export type TerritoryAid = {
  target_type: string
  target_id: string
  player_id: string
  created_at: string
}

export type ChatMessage = {
  id: string
  channel: 'global' | 'nearby' | 'alliance' | 'private'
  author_id: string
  body: string
  flagged: boolean
  created_at: string
}

export type MarketOrder = {
  filled_amount?: number
  id: string
  player_id: string
  side: 'buy' | 'sell'
  resource: string
  amount: number
  price: number
  fee: number
  status: 'open' | 'filled' | 'cancelled'
  created_at: string
}

export function getAllianceProfile() {
  return request<{ profile: AllianceProfile }>('/alliances/me')
}

export function createAlliance(name: string) {
  return request<{ profile: AllianceProfile }>('/alliances', {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function inviteToAlliance(player_id: string) {
  return request<{ invite: AllianceInvite }>('/alliances/invites', { method: 'POST', body: JSON.stringify({ player_id }) })
}

export function respondToAllianceInvite(id: string, accept: boolean) {
  return request<{ profile: AllianceProfile }>(`/alliances/invites/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ accept }) })
}

export function donateToAlliance(input: { resource: string; amount: number }) {
  return request<{ profile: AllianceProfile }>('/alliances/treasury/donations', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function upgradeAllianceBuff(buff_id: string) {
  return request<{ profile: AllianceProfile }>('/alliances/buffs', {
    method: 'POST',
    body: JSON.stringify({ buff_id }),
  })
}

export function listChatMessages(channel: ChatMessage['channel'], before?: string) {
  return request<{ messages: ChatMessage[]; read_state?: { read_at: string; unread: number }; next_cursor?: string }>(`/chat/messages?channel=${encodeURIComponent(channel)}&limit=60${before ? `&before=${encodeURIComponent(before)}` : ''}`)
}

export function sendChatMessage(input: { channel: ChatMessage['channel']; body: string; recipient?: string }) {
  return request<{ message: ChatMessage }>('/chat/messages', {
    method: 'POST',
    body: JSON.stringify({ channel: input.channel, body: input.body, recipient: input.recipient ?? '' }),
  })
}

export function listMarketOrders() {
  return request<{ orders: MarketOrder[] }>('/market/orders')
}

export function createMarketOrder(input: { side: MarketOrder['side']; resource: string; amount: number; price: number }) {
  return request<{ order: MarketOrder }>('/market/orders', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function cancelMarketOrder(id: string) {
  return request<{ order: MarketOrder }>(`/market/orders/${id}`, { method: 'DELETE' })
}

export function leaveAlliance() { return request('/alliances/me', { method: 'DELETE' }) }
export function kickAllianceMember(id: string) { return request(`/alliances/members/${encodeURIComponent(id)}`, { method: 'DELETE' }) }

export function markChatRead(channel: ChatMessage['channel'], message_id: string) {
  return request('/chat/read', { method: 'PATCH', body: JSON.stringify({ channel, message_id }) })
}

export function transferAllianceLeadership(id: string) { return request(`/alliances/members/${encodeURIComponent(id)}/leadership`, { method: 'POST', body: '{}' }) }

export function spendAllianceTreasury(input: { resource: string; amount: number; recipient: string }) {
 return request<{ profile: AllianceProfile }>('/alliances/treasury/spend', { method: 'POST', body: JSON.stringify(input) })
}
