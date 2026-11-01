export type Ownership = 'own' | 'ally' | 'foreign' | 'neutral'
export const ownershipLabels: Record<Ownership, string> = { own: 'Свой объект', ally: 'Союзный объект', foreign: 'Чужой объект', neutral: 'Нейтральный объект' }

export function ownershipOf(ownerId: string | null | undefined, viewerId: string | null | undefined, alliedIds: ReadonlySet<string>): Ownership {
  if (!ownerId) return 'neutral'
  if (ownerId === viewerId) return 'own'
  return alliedIds.has(ownerId) ? 'ally' : 'foreign'
}
