import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useState } from 'react'

import { listChatMessages, sendChatMessage, type ChatMessage } from '../../shared/api/social'

const channels = [
  { id: 'global', label: 'Общий' },
  { id: 'nearby', label: 'Рядом' },
  { id: 'alliance', label: 'Союз' },
] as const

export function ChatPanel() {
  const [channel, setChannel] = useState<ChatMessage['channel']>('global')
  const [body, setBody] = useState('')
  const queryClient = useQueryClient()
  const messagesQuery = useQuery({ queryKey: ['chat', channel], queryFn: () => listChatMessages(channel), refetchInterval: 5000 })
  const sendMutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: () => {
      setBody('')
      void queryClient.invalidateQueries({ queryKey: ['chat', channel] })
    },
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (body.trim()) {
      sendMutation.mutate({ channel, body })
    }
  }

  return (
    <section className="chat-panel" aria-label="Чат">
      <div className="chat-channels">
        {channels.map((item) => (
          <button key={item.id} type="button" aria-pressed={channel === item.id} onClick={() => setChannel(item.id)}>
            {item.label}
          </button>
        ))}
      </div>
      <div className="chat-messages" aria-live="polite">
        {messagesQuery.data?.messages.length ? (
          messagesQuery.data.messages.map((message) => (
            <p key={message.id}>
              <strong>{message.author_id}</strong> {message.flagged ? <em>на модерации</em> : message.body}
            </p>
          ))
        ) : (
          <p>Сообщений пока нет.</p>
        )}
      </div>
      <form className="chat-compose" onSubmit={submit}>
        <input value={body} maxLength={500} aria-label="Сообщение в чат" onChange={(event) => setBody(event.target.value)} />
        <button type="submit" disabled={sendMutation.isPending}>Отправить</button>
      </form>
    </section>
  )
}
