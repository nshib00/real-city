import { FormEvent, useState } from 'react'

import { ApiClientError } from '../../shared/api/client'
import { login, register } from './api'
import { useAuthStore } from './useAuthStore'

type Mode = 'login' | 'register'

export function AuthScreen() {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setSubmitting] = useState(false)
  const setPlayer = useAuthStore((state) => state.setPlayer)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const result =
        mode === 'login'
          ? await login({ email, password })
          : await register({ email, name, password })
      setPlayer(result.player)
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Не удалось выполнить вход')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel" aria-label="Аккаунт">
        <div className="auth-tabs" role="tablist">
          <button
            aria-selected={mode === 'login'}
            className={mode === 'login' ? 'active' : ''}
            onClick={() => setMode('login')}
            type="button"
          >
            Вход
          </button>
          <button
            aria-selected={mode === 'register'}
            className={mode === 'register' ? 'active' : ''}
            onClick={() => setMode('register')}
            type="button"
          >
            Регистрация
          </button>
        </div>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Email
            <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </label>
          {mode === 'register' ? (
            <label>
              Имя города
              <input maxLength={32} minLength={3} onChange={(event) => setName(event.target.value)} required value={name} />
            </label>
          ) : null}
          <label>
            Пароль
            <input
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={10}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {error ? <p className="auth-error">{error}</p> : null}
          <button className="auth-submit" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Отправка...' : mode === 'login' ? 'Войти' : 'Создать город'}
          </button>
        </form>
      </section>
    </main>
  )
}
