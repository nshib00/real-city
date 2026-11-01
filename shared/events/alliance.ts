export type AllianceEventType =
  | 'alliance.created'
  | 'alliance.leader.changed'
  | 'alliance.invite.responded'
  | 'alliance.member.left'
  | 'alliance.member.kicked'
  | 'alliance.invite.created'
  | 'alliance.invite.accepted'
  | 'alliance.invite.declined'
  | 'alliance.role.changed'
  | 'alliance.treasury.donated'
  | 'alliance.treasury.spent'
  | 'alliance.buff.upgraded'
  | 'alliance.territory_aid.added'

export type AllianceEventPayload = {
  alliance_id: string
  player_id?: string
  target_player_id?: string
  role?: 'leader' | 'deputy' | 'officer' | 'member'
  treasurer?: boolean
  resource?: string
  amount?: number
  buff_id?: string
  level?: number
  target_type?: string
  target_id?: string
}
