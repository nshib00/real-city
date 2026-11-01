export type ProfileAppearance = {
 avatar_id: string
 banner_id: string
 title: string
}
export type PublicPlayerProfile = ProfileAppearance & {
 player_id: string
 display_name: string
 level: number
 group_id?: string
 scores: Record<string, number>
 settlement_region?: { district_x: number; district_y: number }
}
