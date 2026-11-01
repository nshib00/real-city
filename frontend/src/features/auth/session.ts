import { getMe } from './api'

// Один запрос на проверку, в том числе при повторном эффекте React StrictMode.
let pending: ReturnType<typeof getMe> | null = null
export function restoreSession() {
  if (!pending) pending = getMe().finally(() => { pending = null })
  return pending
}
