import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useEffect, useRef, useState } from 'react'

import { listChatMessages, markChatRead, sendChatMessage, type ChatMessage } from '../../shared/api/social'
import { chatSoundEnabled, isMention, playChatSound, setChatSoundEnabled } from '../../audio/socialAudio'
import { useAuthStore } from '../auth/useAuthStore'
import { useGameStore } from '../../game/state/useGameStore'
import { chatChannels as channels, useChatChannels } from './useChatChannels'

export function ChatPanel({ visible = true }: { visible?: boolean }) {
  const [channel, setChannel] = useState<ChatMessage['channel']>('global')
  const [drafts, setDrafts] = useState<Partial<Record<ChatMessage['channel'], string>>>({})
  const body = drafts[channel] ?? ''
  const setBody = (body: string) => setDrafts((current) => ({ ...current, [channel]: body }))
  const [history, setHistory] = useState<ChatMessage[]>([])
  const [historyCursor, setHistoryCursor] = useState<string | undefined>()
  const [historyOwner, setHistoryOwner] = useState('')
  const [soundEnabled, setSoundEnabled] = useState(chatSoundEnabled)
  const player = useAuthStore((state) => state.player)
  const realtimeStatus = useGameStore((state) => state.realtimeStatus)
  const seenByChannel = useRef(new Map<ChatMessage['channel'], Set<string>>())
  const queryClient = useQueryClient()
  const channelQueries = useChatChannels()
  const messagesQuery = channelQueries[channels.findIndex((item) => item.id === channel)]
  const historyMutation = useMutation({
    mutationFn: ({ channel, cursor }: { channel: ChatMessage['channel']; cursor: string; playerId: string }) => listChatMessages(channel, cursor),
    onSuccess: (data, input) => {
      if (input.channel !== channel || input.playerId !== player?.id) return
      setHistoryOwner(`${input.playerId}:${input.channel}`)
      setHistory((current) => [...current, ...data.messages.filter((message) => !current.some((old) => old.id === message.id))])
      setHistoryCursor(data.next_cursor ?? '')
    },
  })
  useEffect(() => { setHistory([]); setHistoryCursor(undefined) }, [channel, player?.id])
  const currentMessages = messagesQuery.data?.messages ?? []
  const ownsHistory = historyOwner === `${player?.id}:${channel}`
  const messages = [...currentMessages, ...(ownsHistory ? history : []).filter((message) => !currentMessages.some((latest) => latest.id === message.id))]
  const nextCursor = (ownsHistory ? historyCursor : undefined) ?? messagesQuery.data?.next_cursor
  const readMutation = useMutation({
    mutationFn: ({ channel, id }: { channel: ChatMessage['channel']; id: string }) => markChatRead(channel, id),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['chat'] }) },
  })
  const lastRead = useRef('')
  useEffect(() => { seenByChannel.current.clear(); lastRead.current = ''; setDrafts({}) }, [player?.id])
  useEffect(() => {
    const mark = () => {
      const latest = messagesQuery.data?.messages[0]
      const key = `${player?.id}:${channel}:${latest?.id}`
      if (!visible || !player || document.hidden || !latest || lastRead.current === key || readMutation.isPending || !messagesQuery.data?.read_state?.unread) return
      lastRead.current = key
      readMutation.mutate({ channel, id: latest.id })
    }
    mark()
    document.addEventListener('visibilitychange', mark)
    return () => document.removeEventListener('visibilitychange', mark)
  }, [visible, channel, player?.id, messagesQuery.data, readMutation.isPending])
  const sendMutation = useMutation({
    mutationFn: (input: { channel: ChatMessage['channel']; body: string; playerId: string }) => sendChatMessage({ channel: input.channel, body: input.body }),
    onSuccess: (_data, input) => {
      if (useAuthStore.getState().player?.id !== input.playerId) return
      playChatSound('social.chat.sent')
      setDrafts((current) => current[input.channel] === input.body ? { ...current, [input.channel]: '' } : current)
      void queryClient.invalidateQueries({ queryKey: ['chat', input.channel] })
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
    if (body.trim() && player && !sendMutation.isPending) {
      sendMutation.mutate({ channel, body, playerId: player.id })
    }
  }

  return (
    <section className="chat-panel" aria-label="Чат">
      {realtimeStatus !== 'connected' ? <p className="connection-note" role="status">Нет постоянного соединения с миром. Чат обновляется отдельными запросами; проверьте связь, если отправка не удаётся.</p> : null}
      <label><input type="checkbox" checked={soundEnabled} onChange={(event) => { setSoundEnabled(event.target.checked); setChatSoundEnabled(event.target.checked) }} /> Уведомления чата</label>
      <div className="chat-channels">
        {channels.map((item, index) => (
          <button key={item.id} type="button" aria-pressed={channel === item.id} onClick={() => setChannel(item.id)}>
            {item.label}{channelQueries[index].data?.read_state?.unread ? ` (${channelQueries[index].data?.read_state?.unread})` : ''}
          </button>
        ))}
      </div>
      {messagesQuery.error ? <p role="alert">{messagesQuery.error.message} <button type="button" onClick={() => void messagesQuery.refetch()}>Повторить</button></p> : null}
      {readMutation.error ? <p role="alert">Не удалось отметить сообщения прочитанными. <button type="button" onClick={() => {
        const latest = messagesQuery.data?.messages[0]
        if (latest && !document.hidden) readMutation.mutate({ channel, id: latest.id })
      }}>Повторить отметку</button></p> : null}
      {messagesQuery.isPending ? <p role="status">Загружаем сообщения…</p> : null}
      <div className="chat-messages" aria-label="История сообщений">
        {messages.length ? (
          messages.map((message) => (
            <p key={message.id}>
              <strong>{message.author_id}</strong> {message.flagged ? <em>на модерации</em> : message.body}
            </p>
          ))
        ) : (
          !messagesQuery.isPending && !messagesQuery.error ? <p>Сообщений пока нет.</p> : null
        )}
      </div>
      {nextCursor ? <button type="button" disabled={historyMutation.isPending || !player} onClick={() => historyMutation.mutate({ channel, cursor: nextCursor, playerId: player?.id ?? '' })}>Загрузить предыдущие сообщения</button> : null}
      {historyMutation.error ? <p role="status">{historyMutation.error.message}</p> : null}
      <form className="chat-compose" onSubmit={submit}>
        <input value={body} maxLength={500} aria-label="Сообщение в чат" onChange={(event) => setBody(event.target.value)} />
        <button type="submit" disabled={sendMutation.isPending || !body.trim()}>Отправить</button>
      </form>
      {sendMutation.error ? <p role="alert">Сообщение не отправлено: {sendMutation.error.message}. Текст сохранён, попробуйте снова.</p> : null}
    </section>
  )
}
