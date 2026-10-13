export const MAX_ACTIVE_THREE_PREVIEWS = 3

let activeThreePreviews = 0

export function acquireThreePreviewSlot() {
  if (activeThreePreviews >= MAX_ACTIVE_THREE_PREVIEWS) {
    return false
  }
  activeThreePreviews += 1
  return true
}

export function releaseThreePreviewSlot() {
  activeThreePreviews = Math.max(0, activeThreePreviews - 1)
}

export function activeThreePreviewCount() {
  return activeThreePreviews
}

export function resetThreePreviewBudgetForTests() {
  activeThreePreviews = 0
}
