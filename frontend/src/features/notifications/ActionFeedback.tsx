import { useEffect, useState } from 'react'
import { useIsMutating, useQueryClient } from '@tanstack/react-query'
import { ActionState, actionErrorReason, type ActionPhase } from '../../shared/ui/ActionState'
import { setInterfaceTheme, useInterfaceTheme } from '../../app/theme'

export function ActionFeedback() {
  const theme = useInterfaceTheme()
  const client = useQueryClient()
  const pending = useIsMutating()
  const [online, setOnline] = useState(() => navigator.onLine)
  const [feedback, setFeedback] = useState<{ phase: ActionPhase; reason?: string } | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [effects, setEffects] = useState(() => {
    try { return localStorage.getItem('real-city.ui-effects') !== 'off' } catch { return true }
  })
  useEffect(() => {
    const update = () => setOnline(navigator.onLine)
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update) }
  }, [])
  useEffect(() => {
    document.documentElement.dataset.uiEffects = effects ? 'on' : 'off'
    try { localStorage.setItem('real-city.ui-effects', effects ? 'on' : 'off') } catch { /* Настройка работает и без хранилища. */ }
    return () => { delete document.documentElement.dataset.uiEffects }
  }, [effects])
  useEffect(() => client.getMutationCache().subscribe((event) => {
    if (event.type !== 'updated') return
    if (event.action.type === 'pending') setFeedback({ phase: 'pending' })
    if (event.action.type === 'success') setFeedback({ phase: 'success' })
    if (event.action.type === 'error') {
      const error = event.mutation.state.error
      setFeedback(error instanceof Error && error.name === 'AbortError'
        ? { phase: 'cancelled', reason: 'Запрос прерван. Проверьте состояние объекта: сервер мог уже принять действие.' }
        : { phase: 'error', reason: actionErrorReason(error) })
    }
  }), [client])
  return <aside className="action-feedback" aria-label="Ответ сервера и эффекты">
    {!online ? <ActionState phase="offline" reason="Проверьте соединение. Не повторяйте запрос, пока не проверите результат в мире." /> : pending > 0 ? <ActionState phase="pending" reason={`Запросов в очереди: ${pending}. Ресурсы и результат обновятся после ответа сервера.`} /> : feedback && <ActionState {...feedback} />}
    <details className="interface-settings" open={settingsOpen} onToggle={(event) => setSettingsOpen(event.currentTarget.open)}>
    <summary>Интерфейс</summary>
    <button type="button" aria-pressed={effects} onClick={() => setEffects(!effects)}>Эффекты: {effects ? 'включены' : 'выключены'}</button>
    <label className="interface-theme-control">Оформление<select value={theme} onChange={(event) => setInterfaceTheme(event.target.value === 'aeolian' ? 'aeolian' : 'classic')}><option value="classic">Классическое</option><option value="aeolian">Эолия</option></select></label>
    </details>
  </aside>
}
