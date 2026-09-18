export type ChatEventType = 'chat.message.created' | 'chat.message.flagged'

export type ChatMessagePayload = {
  id: string
  channel: 'global' | 'nearby' | 'alliance' | 'private'
  author_id: string
  alliance_id?: string
  recipient?: string
  body: string
  flagged: boolean
  created_at: string
}
