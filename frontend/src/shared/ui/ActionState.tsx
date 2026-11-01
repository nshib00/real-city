import { ApiClientError } from '../api/client'
import { AeolianIcon } from './AeolianIcon'

export type ActionPhase = 'ready' | 'blocked' | 'pending' | 'success' | 'error' | 'cancelled' | 'cooldown' | 'offline'
const labels: Record<ActionPhase, string> = {
  ready: 'Готово к действию', blocked: 'Действие недоступно', pending: 'Ожидаем ответ сервера',
  success: 'Сервер подтвердил действие', error: 'Действие не выполнено', cancelled: 'Действие отменено',
  cooldown: 'Действие восстанавливается', offline: 'Нет связи — подтверждение сервера недоступно',
}
const icons: Record<ActionPhase, string> = { ready: 'check', blocked: 'lock', pending: 'clock', success: 'check', error: 'damage', cancelled: 'cancel', cooldown: 'clock', offline: 'offline' }
const reasons = {
  bad_request: 'Проверьте параметры действия.', validation: 'Условия действия не выполнены.',
  unauthorized: 'Войдите в игру заново.', forbidden: 'Нет разрешения на действие.',
  not_found: 'Объект больше недоступен.', conflict: 'Состояние мира изменилось. Проверьте объект и повторите действие.',
  rate_limited: 'Слишком много запросов. Подождите перед повторной попыткой.', internal: 'Ошибка сервера. Попробуйте позже.',
}

export function actionErrorReason(error: unknown): string {
  // Не выводим произвольные payload/сообщения: они могут содержать личные данные.
  return error instanceof ApiClientError ? reasons[error.apiError.kind] ?? 'Сервер отклонил действие.' : 'Не удалось получить подтверждение. Проверьте соединение и состояние объекта перед повтором.'
}

export function ActionState({ phase, reason, announce = true }: { phase: ActionPhase; reason?: string; announce?: boolean }) {
  return <div className={`action-state action-state-${phase}`} data-phase={phase} role={announce ? 'status' : undefined} aria-atomic="true">
    <strong><AeolianIcon name={icons[phase]} size={16} /> {labels[phase]}</strong>{reason && <span>{reason}</span>}
  </div>
}
