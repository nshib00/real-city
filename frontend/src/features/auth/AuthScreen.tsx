import { FormEvent, useRef, useState } from 'react'

import { ApiClientError } from '../../shared/api/client'
import { login, register } from './api'
import { useAuthStore } from './useAuthStore'
import { ServerStatus } from './ServerStatus'
import { useAuthViewport } from './useAuthViewport'

type Mode = 'login' | 'register'
const fieldMessages: Record<string, string> = {
  'may contain letters, numbers, spaces, underscores and hyphens': 'Используйте латинские буквы, цифры, пробел, дефис или подчёркивание.',
  'must be between 3 and 32 characters': 'Введите от 3 до 32 символов.',
  'must include letters and numbers': 'Добавьте буквы и цифры.',
}

export function AuthScreen({ expired = false }: { expired?: boolean }) {
  useAuthViewport()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [useSceneFallback, setUseSceneFallback] = useState(false)
  const [sceneUnavailable, setSceneUnavailable] = useState(false)
  const [fields, setFields] = useState<Record<string, string>>({})
  const submitting = useRef(false)
  const emailRef = useRef<HTMLInputElement>(null)
  const setPlayer = useAuthStore((state) => state.setPlayer)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (submitting.current) return
    submitting.current = true
    setError('')
    setFields({})
    setSubmitting(true)
    try {
      const result =
        mode === 'login'
          ? await login({ email, password })
          : await register({ email, name, password })
      setPlayer(result.player)
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Не удалось связаться с сервером. Проверьте соединение и повторите отправку.')
      if (err instanceof ApiClientError) {
        const nextFields = Object.fromEntries(Object.entries(err.apiError.fields ?? {}).map(([field, message]) => [field, fieldMessages[message] ?? message]))
        setFields(nextFields)
        if (Object.keys(nextFields).length) setError('Проверьте отмеченные поля.')
      }
    } finally {
      submitting.current = false
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-screen start-screen">
      <figure className="start-scene">
        {sceneUnavailable ? <div className="start-scene-fallback" role="img" aria-label="Карта Эолии загрузится после входа" /> :
          <picture>
            {!useSceneFallback ? <>
              <source media="(max-width: 700px)" type="image/webp" srcSet="/assets/ui/start/settlement-480.webp" />
              <source type="image/webp" srcSet="/assets/ui/start/settlement-960.webp" />
            </> : null}
            <img
              src={useSceneFallback ? '/assets/ui/start/settlement-480.webp' : '/assets/ui/start/settlement-960.webp'}
              width="960"
              height="656"
              alt="Изометрический участок Эолии с ратушей, домами, дорогой, садом и лесом"
              fetchPriority="high"
              onError={() => useSceneFallback ? setSceneUnavailable(true) : setUseSceneFallback(true)}
            />
          </picture>}
        <figcaption>Место для вашего города есть в общем мире.</figcaption>
      </figure>
      <section className="auth-panel start-panel" aria-label="Аккаунт">
        <div className="start-brand">
          <img src="/assets/ui/start/eolia-mark.png" width="64" height="64" alt="" aria-hidden="true" />
          <h1>Эолия</h1>
        </div>
        <p className="start-promise">Строй город в общем живом мире</p>
        <ul className="start-principles"><li>Строй рядом с другими игроками.</li><li>Добывай ресурсы и развивай производство.</li><li>Защищай постройки и пути к запасам.</li></ul>
        <div className="start-actions"><button type="button" disabled={isSubmitting} onClick={() => { setMode('register'); setError(''); setFields({}); emailRef.current?.focus() }}>Начать играть</button><button type="button" disabled={isSubmitting} onClick={() => { setMode('login'); setError(''); setFields({}); emailRef.current?.focus() }}>Войти в аккаунт</button></div>
        {expired ? <p role="status">Сессия истекла. Войдите снова, чтобы вернуться к карте.</p> : null}
        <div className="auth-tabs" role="group" aria-label="Способ входа">
          <button
            aria-pressed={mode === 'login'}
            className={mode === 'login' ? 'active' : ''}
            onClick={() => { setMode('login'); setError(''); setFields({}) }}
            disabled={isSubmitting}
            type="button"
          >
            Вход
          </button>
          <button
            aria-pressed={mode === 'register'}
            className={mode === 'register' ? 'active' : ''}
            onClick={() => { setMode('register'); setError(''); setFields({}) }}
            disabled={isSubmitting}
            type="button"
          >
            Регистрация
          </button>
        </div>
        <form className="auth-form" onSubmit={onSubmit} aria-busy={isSubmitting}>
          <label>
            Email
            <input ref={emailRef} autoComplete="username" inputMode="email" disabled={isSubmitting} aria-invalid={Boolean(fields.email)} aria-describedby={fields.email ? 'auth-email-error' : undefined} onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </label>
          {fields.email ? <small id="auth-email-error" className="auth-error">{fields.email}</small> : null}
          {mode === 'register' ? <>
            <label>
              Имя города
              <input autoComplete="nickname" disabled={isSubmitting} aria-invalid={Boolean(fields.name)} aria-describedby={fields.name ? 'auth-name-help auth-name-error' : 'auth-name-help'} maxLength={32} minLength={3} onChange={(event) => setName(event.target.value)} required value={name} />
            </label>
            <small id="auth-name-help">3–32 символа: латинские буквы, цифры, пробел, дефис или подчёркивание.</small>
            {fields.name ? <small id="auth-name-error" className="auth-error">{fields.name}</small> : null}
          </> : null}
          <label>
            Пароль
            <input
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={mode === 'register' ? 10 : undefined}
              disabled={isSubmitting}
              id="auth-password"
              aria-invalid={Boolean(fields.password)}
              aria-describedby={fields.password ? 'auth-password-error' : mode === 'register' ? 'auth-password-help' : undefined}
              onChange={(event) => setPassword(event.target.value)}
              required
              type={showPassword ? 'text' : 'password'}
              value={password}
            />
          </label>
          <button type="button" aria-controls="auth-password" aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Скрыть пароль' : 'Показать пароль'}</button>
          {mode === 'register' ? <small id="auth-password-help">Не менее 10 символов.</small> : null}
          {fields.password ? <small id="auth-password-error" className="auth-error">{fields.password}</small> : null}
          {error ? <p className="auth-error" role="alert">{error}</p> : null}
          <button className="auth-submit" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Отправка...' : mode === 'login' ? 'Войти' : 'Создать город'}
          </button>
        </form>
        <ServerStatus />
      </section>
    </main>
  )
}
