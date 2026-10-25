import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useEffect, useRef, useState } from 'react'

import { listChatMessages, sendChatMessage, type ChatMessage } from '../../shared/api/social'
import { chatSoundEnabled, isMention, playChatSound, setChatSoundEnabled } from '../../audio/socialAudio'
import { useAuthStore } from '../auth/useAuthStore'

const channels = [
  { id: 'global', label: 'Общий' },
  { id: 'nearby', label: 'Рядом' },
  { id: 'alliance', label: 'Союз' },
] as const

export function ChatPanel() {
  const [channel, setChannel] = useState<ChatMessage['channel']>('global')
  const [body, setBody] = useState('')
  const [soundEnabled, setSoundEnabled] = useState(chatSoundEnabled)
  const player = useAuthStore((state) => state.player)
  const seenByChannel = useRef(new Map<ChatMessage['channel'], Set<string>>())
  const queryClient = useQueryClient()
  const messagesQuery = useQuery({ queryKey: ['chat', channel], queryFn: () => listChatMessages(channel), refetchInterval: 5000 })
  const sendMutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: () => {
      playChatSound('social.chat.sent')
      setBody('')
      void queryClient.invalidateQueries({ queryKey: ['chat', channel] })
    },
  })

  useEffect(() => {
    const messages = messagesQuery.data?.messages
    if (!messages) return
    const seen = seenByChannel.current.get(channel)
    if (!seen) {
      seenByChannel.current.set(channel, new Set(messages.map((message) => message.id)))
      return
    }
    const fresh = messages.filter((message) => !seen.has(message.id))
    for (const message of messages) seen.add(message.id)
    if (seen.size > 200) seenByChannel.current.set(channel, new Set(messages.map((message) => message.id)))
    const incoming = fresh.filter((message) => message.author_id !== player?.id && !message.flagged)
    if (!incoming.length) return
    const names = [player?.name ?? '', player?.profile.display_name ?? '']
    playChatSound(incoming.some((message) => isMention(message.body, names)) ? 'social.chat.mention' : 'social.chat.received')
  }, [channel, messagesQuery.data, player])

  function submit(event: FormEvent) {
    event.preventDefault()
    if (body.trim()) {
      sendMutation.mutate({ channel, body })
    }
  }

  return (
    <section className="chat-panel" aria-label="Чат">
      <label><input type="checkbox" checked={soundEnabled} onChange={(event) => { setSoundEnabled(event.target.checked); setChatSoundEnabled(event.target.checked) }} /> Уведомления чата</label>
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
