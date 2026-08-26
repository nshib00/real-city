import { useEffect, useState } from 'react'

import { clearTokens, getAccessToken } from '../../shared/api/client'
import { StatusState } from '../../shared/ui/StatusState'
import { getMe, refresh } from './api'
import { AuthScreen } from './AuthScreen'
import { useAuthStore } from './useAuthStore'

type AuthGateProps = {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const { isAuthenticated, setPlayer } = useAuthStore()
  const [isBooting, setBooting] = useState(Boolean(getAccessToken()))

  useEffect(() => {
    if (!getAccessToken()) {
      setBooting(false)
      return
    }
    getMe()
      .then(setPlayer)
      .catch(() => refresh().then((result) => setPlayer(result.player)))
      .catch(() => {
        clearTokens()
        setPlayer(null)
      })
      .finally(() => setBooting(false))
  }, [setPlayer])

  if (isBooting) {
    return <StatusState>Подключение сессии</StatusState>
  }

  if (!isAuthenticated) {
    return <AuthScreen />
  }

  return children
}
