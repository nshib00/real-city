import { useEffect, useState } from 'react'

import { ApiClientError, clearTokens, getAccessToken } from '../../shared/api/client'
import { StatusState } from '../../shared/ui/StatusState'
import { restoreSession } from './session'
import { AuthScreen } from './AuthScreen'
import { useAuthStore } from './useAuthStore'

type AuthGateProps = {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const { isAuthenticated, setPlayer } = useAuthStore()
  const [isBooting, setBooting] = useState(Boolean(getAccessToken()))
  const [error, setError] = useState(false)
  const [expired, setExpired] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (!getAccessToken()) {
      setBooting(false)
      return
    }
    let active = true
    setBooting(true)
    setError(false)
    restoreSession()
      .then(player => { if (active) setPlayer(player) })
      .catch((err: unknown) => {
        if (!active) return
        if (err instanceof ApiClientError && (err.apiError.kind === 'unauthorized' || !getAccessToken())) {
          clearTokens()
          setPlayer(null)
          setExpired(true)
        } else setError(true)
      })
      .finally(() => { if (active) setBooting(false) })
    return () => { active = false }
  }, [setPlayer, attempt])

  if (error) return <StatusState title="Не удалось проверить сессию" variant="error" action={{ label: 'Повторить подключение', onClick: () => setAttempt(attempt + 1) }}>Проверьте соединение. Ваша сессия сохранена; повтор не создаёт новый аккаунт.</StatusState>

  if (isBooting) {
    return <StatusState>Подключение сессии</StatusState>
  }

  if (!isAuthenticated) {
    return <AuthScreen expired={expired} />
  }

  return children
}
