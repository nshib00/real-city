import { playUiSound } from './playUiSound'
import { getAudioSettings, updateAudioSettings } from './audioSettings'

const chatKey = 'real-city.audio.chat-enabled'
let chatEnabledFallback = true

export function chatSoundEnabled(): boolean {
  return getAudioSettings().chat
}

export function setChatSoundEnabled(enabled: boolean): void {
  chatEnabledFallback = enabled
  updateAudioSettings({ chat: enabled })
  try { localStorage.setItem(chatKey, String(enabled)) } catch { /* Настройка действует до перезагрузки. */ }
}

export function playChatSound(id: 'social.chat.received' | 'social.chat.sent' | 'social.chat.mention'): void {
  if (chatSoundEnabled()) playUiSound(id, undefined, id === 'social.chat.mention' ? 0.7 : 0.4)
}

export function isMention(body: string, names: readonly string[]): boolean {
  return names.some((name) => {
    const escaped = name.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return escaped.length > 0 && new RegExp(`(^|\\s)@${escaped}(?=$|[\\s.,!?;:])`, 'iu').test(body)
  })
}
