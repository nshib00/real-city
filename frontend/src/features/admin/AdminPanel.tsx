import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Shield } from '../../shared/ui/icons'

import { useAuthStore } from '../auth/useAuthStore'
import { request } from '../../shared/api/client'
import { IconButton, Modal } from '../../shared/ui'

type PendingMessage = { id: string; channel: string; author_id: string; body: string }
type Audit = { id: string; actor_id: string; message_id: string; action: string; reason: string; created_at: string }
type AccountAudit = { id: string; actor_id: string; player_id: string; status: string; role: string; reason: string; created_at: string }

export function AdminPanel() {
  const role = useAuthStore((state) => state.player?.role)
  return role === 'admin' ? <AdminControls /> : null
}

function AdminControls() {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState('')
  const player = useAuthStore((state) => state.player)
  const client = useQueryClient()
  const enabled = open && player?.role === 'admin'
  const players = useQuery({ queryKey: ['admin', 'players', player?.id], queryFn: () => request<{ players: { id: string; name: string; status: string; role: string }[] }>('/admin/players'), enabled })
  const messages = useQuery({ queryKey: ['admin', 'messages', player?.id], queryFn: () => request<{ messages: PendingMessage[] }>('/admin/chat/messages'), enabled })
  const audit = useQuery({ queryKey: ['admin', 'audit', player?.id], queryFn: () => request<{ actions: Audit[] }>('/admin/audit'), enabled })
  const accounts = useQuery({ queryKey: ['admin', 'accounts', player?.id], queryFn: () => request<{ actions: AccountAudit[] }>('/admin/accounts/audit'), enabled })
  const changeAccount = useMutation({
    mutationFn: ({ id, status, role }: { id: string; status: string; role: string }) => request(`/admin/players/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ status, role, reason }) }),
    onSuccess: () => { setReason(''); void client.invalidateQueries({ queryKey: ['admin'] }) },
  })
  const moderate = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approve' | 'reject' }) => request(`/admin/chat/messages/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ action, reason }) }),
    onSuccess: () => { setReason(''); void client.invalidateQueries({ queryKey: ['admin'] }); void client.invalidateQueries({ queryKey: ['chat'] }) },
  })
  if (player?.role !== 'admin') return null
  return <>
    <IconButton label="Администрирование" icon={Shield} onClick={() => setOpen(true)} />
    <Modal title="Администрирование" open={open} onClose={() => setOpen(false)}>
      <h3>Игроки</h3>
      <label>Причина изменения аккаунта или решения модератора <input aria-label="Причина решения" value={reason} maxLength={500} onChange={(event) => setReason(event.target.value)} /></label>
      {players.data?.players.map((item) => <article key={item.id}>
        <p>{item.name} ({item.id}) — {item.status}, {item.role}</p>
        <button type="button" disabled={reason.trim().length < 3 || changeAccount.isPending} onClick={() => changeAccount.mutate({ id: item.id, status: item.status === 'suspended' ? 'active' : 'suspended', role: item.role })}>{item.status === 'suspended' ? 'Разблокировать' : 'Заблокировать'} {item.name}</button>
        <button type="button" disabled={reason.trim().length < 3 || changeAccount.isPending} onClick={() => changeAccount.mutate({ id: item.id, status: item.status, role: item.role === 'admin' ? 'user' : 'admin' })}>{item.role === 'admin' ? 'Снять роль администратора:' : 'Назначить администратором:'} {item.name}</button>
      </article>)}
      <h3>Модерация чата</h3>
      {!messages.isPending && !messages.data?.messages.length ? <p>Очередь модерации пуста.</p> : null}
      {messages.data?.messages.map((message) => <article key={message.id}>
        <p>{message.author_id} · {message.channel}: {message.body}</p>
        <button type="button" disabled={reason.trim().length < 3 || moderate.isPending} onClick={() => moderate.mutate({ id: message.id, action: 'approve' })}>Разрешить сообщение</button>
        <button type="button" disabled={reason.trim().length < 3 || moderate.isPending} onClick={() => moderate.mutate({ id: message.id, action: 'reject' })}>Удалить текст сообщения</button>
      </article>)}
      <h3>Журнал решений</h3>
      {audit.data?.actions.map((item) => <p key={item.id}>{new Date(item.created_at).toLocaleString('ru-RU')} · {item.actor_id} · {item.action} · {item.message_id}: {item.reason}</p>)}
      <h3>Изменения аккаунтов</h3>
      {accounts.data?.actions.map((item) => <p key={item.id}>{new Date(item.created_at).toLocaleString('ru-RU')} · {item.actor_id} → {item.player_id} · {item.status}, {item.role}: {item.reason}</p>)}
      {players.error || messages.error || audit.error || accounts.error || moderate.error || changeAccount.error ? <p role="alert">Не удалось выполнить административный запрос. Проверьте соединение и права доступа.</p> : null}
    </Modal>
  </>
}
