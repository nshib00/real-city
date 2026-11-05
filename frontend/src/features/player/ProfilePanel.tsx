import { Bell, LogOut, MonitorCog, Settings, ShieldAlert, Star, UserRound } from '../../shared/ui/icons'
import { useEffect, useRef, useState } from 'react'

import { playUiSound } from '../../audio/playUiSound'
import { getMe, logout, updateMe } from '../auth/api'
import type { RenderQuality } from '../auth/types'
import { useAuthStore } from '../auth/useAuthStore'
import { Modal } from '../../shared/ui/Modal'

import { levelThresholds, playerProgress } from './levels'
import { LevelEmblem } from './LevelEmblem'
import { ProfileScores } from './ProfileScores'

export function ProfilePanel() {
  const { player, setPlayer } = useAuthStore()
  const [profileOpen, setProfileOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [cityName, setCityName] = useState('')
  const [avatarURL, setAvatarURL] = useState('')
  const [title,setTitle]=useState('')
  const [avatarId,setAvatarId]=useState('')
  const [bannerId,setBannerId]=useState('')
  const [quality, setQuality] = useState<RenderQuality>('medium')
  const [attackAlerts, setAttackAlerts] = useState(true)
  const [productionReady, setProductionReady] = useState(true)
  const [marketUpdates, setMarketUpdates] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const lastLevel = useRef<{ playerId: string; level: number } | null>(null)

  useEffect(() => {
    setProfileOpen(false)
    setSettingsOpen(false)
    setSaveError('')
  }, [player?.id])

  useEffect(() => {
    if (!player) { lastLevel.current = null; return }
    const level = levelThresholds.reduce((current, threshold, index) => player.profile.xp >= threshold ? index + 1 : current, 1)
    if (lastLevel.current?.playerId === player.id && level > lastLevel.current.level) playUiSound('economy.level.up')
    lastLevel.current = { playerId: player.id, level }
  }, [player])

  useEffect(() => {
    if (!player?.id) {
      return
    }
    const timer = window.setInterval(() => {
      getMe().then((updated) => {
        if (useAuthStore.getState().player?.id === updated.id) setPlayer(updated)
      }).catch(() => undefined)
    }, 10_000)
    return () => window.clearInterval(timer)
  }, [player?.id, setPlayer])

  useEffect(() => {
    if (!player || settingsOpen) {
      return
    }
    setDisplayName(player.profile.display_name)
    setCityName(player.profile.city_name)
    setAvatarURL(player.profile.avatar_url)
    setTitle(player.profile.title ?? '')
    setAvatarId(player.profile.avatar_id ?? '')
    setBannerId(player.profile.banner_id ?? '')
    setQuality(player.profile.settings.render_quality)
    setAttackAlerts(player.profile.settings.notifications.attack_alerts)
    setProductionReady(player.profile.settings.notifications.production_ready)
    setMarketUpdates(player.profile.settings.notifications.market_updates)
  }, [player, settingsOpen])

  if (!player) {
    return null
  }

  async function saveSettings() {
    if (!player || saving) {
      return
    }
    setSaving(true)
    setSaveError('')
    try {
      const updated = await updateMe({
        display_name: displayName,
        city_name: cityName,
        avatar_url: avatarURL,
        title, avatar_id: avatarId, banner_id: bannerId,
        settings: {
          notifications: {
            attack_alerts: attackAlerts,
            production_ready: productionReady,
            market_updates: marketUpdates,
          },
          render_quality: quality,
        },
      })
      if (useAuthStore.getState().player?.id !== player.id) return
      setPlayer(updated)
      setSettingsOpen(false)
      setProfileOpen(true)
    } catch {
      if (useAuthStore.getState().player?.id === player.id) setSaveError('Не удалось сохранить профиль. Проверьте связь и повторите сохранение.')
    } finally {
      setSaving(false)
    }
  }

  async function onLogout() {
    await logout()
    setPlayer(null)
    setProfileOpen(false)
    setSettingsOpen(false)
  }

  const profile = player.profile
  const avatarLabel = profile.display_name.slice(0, 1).toUpperCase()
  const totalXP = Number.isFinite(profile.xp) ? Math.max(0, profile.xp) : 0
  const level = levelThresholds.reduce((current, threshold, index) => totalXP >= threshold ? index + 1 : current, 1)
  const levelStartXP = levelThresholds[level - 1]
  const nextThreshold = levelThresholds[level]
  const levelXP = totalXP - levelStartXP
  const nextLevelXP = nextThreshold === undefined ? 0 : nextThreshold - levelStartXP
  const remainingXP = nextThreshold === undefined ? 0 : nextThreshold - totalXP
  const progress = playerProgress(totalXP)
  const xpPercent = progress.percent
  const xpLabel = nextLevelXP > 0 ? `${levelXP}/${nextLevelXP}` : `${levelXP}`

  return (
    <>
      <button className="profile-panel" aria-label="Открыть профиль игрока" onClick={() => setProfileOpen(true)} type="button">
        <span className="profile-avatar-stack">
          <span className="profile-avatar" aria-hidden="true">
            {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : avatarLabel}
          </span>
          <span className="profile-level-badge" title={`Уровень ${level}`}>
            <LevelEmblem level={level} size="medium" /> {level}
          </span>
          <span className="profile-xp-mini" aria-hidden="true">
            <span style={{ width: `${xpPercent}%` }} />
          </span>
        </span>
        <span className="profile-main">
          <strong>{profile.display_name}</strong>
          <span>{profile.city_name}</span>
        </span>
      </button>

      <Modal title="Профиль" open={profileOpen} className="profile-modal-backdrop" onClose={() => setProfileOpen(false)}>
        <div className="profile-drawer-body">
          <p className="panel-note">Ваш профиль. Настройки аккаунта доступны только вам; другим игрокам показывается публичная карточка.</p>
          <div className="profile-identity">
            <span className="profile-avatar profile-avatar-large" aria-hidden="true">
              {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : avatarLabel}
            </span>
            <LevelEmblem level={level} size="large" className="profile-level-hero" />
            <div>
              <strong>{profile.display_name}</strong>
              <span>{profile.city_name}</span>
              <span className="profile-level-title">Уровень {level} · {progress.title}</span>
            </div>
          </div>

          {profile.title ? <p>{profile.title}</p> : null}
          <ProfileScores scores={profile.scores} />
          <div className="profile-stat-grid">
            <article>
              <UserRound size={16} />
              <span>Игрок</span>
              <strong>{player.name}</strong>
            </article>
            <article>
              <Star size={16} />
              <span>Уровень</span>
              <strong>{level}</strong>
              <small>{progress.title}</small>
            </article>
            <article>
              <span>XP</span>
              <strong title={`Всего опыта: ${totalXP}`}>{xpLabel}</strong>
            </article>
            <article>
              <span>Роль</span>
              <strong>{player.role}</strong>
            </article>
          </div>

          <p className="profile-level-description">{progress.title}</p>
          <ul aria-label="Возможности уровня">{progress.unlocks.map((unlock) => <li key={unlock.label}>{unlock.label}{unlock.status === 'planned' ? ' — запланировано' : ''}</li>)}</ul>
          <div className="profile-xp-detail" aria-label={`Опыт: ${xpLabel}`}>
            <span>
              <strong>Опыт</strong>
              <em>{xpLabel}</em>
            </span>
            <div>
              <span style={{ width: `${xpPercent}%` }} />
            </div>
            <small>{nextThreshold === undefined ? 'Максимальный уровень' : `До следующего уровня: ${remainingXP} XP`}</small>
          </div>

          <dl className="profile-meta">
            <div>
              <dt>Email</dt>
              <dd>{player.email}</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>{player.status}</dd>
            </div>
            <div>
              <dt>Создан</dt>
              <dd>{formatDate(player.created_at)}</dd>
            </div>
            <div>
              <dt>Профиль обновлен</dt>
              <dd>{formatDate(profile.updated_at)}</dd>
            </div>
          </dl>

          <div className="profile-actions">
            <button
              type="button"
              onClick={() => {
                setProfileOpen(false)
                setSettingsOpen(true)
              }}
            >
              <Settings size={16} /> Настройки
            </button>
            <button type="button" onClick={onLogout}>
              <LogOut size={16} /> Выйти
            </button>
          </div>
        </div>
      </Modal>

      <Modal title="Настройки профиля" open={settingsOpen} className="profile-modal-backdrop" onClose={() => setSettingsOpen(false)}>
        <div className="profile-settings-form">
          <label>
            Имя пользователя
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
          </label>
          <label>
            Название города
            <input value={cityName} onChange={(event) => setCityName(event.target.value)} />
          </label>
          <label>Титул<input maxLength={80} value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Аватар<input maxLength={48} value={avatarId} onChange={(event) => setAvatarId(event.target.value)} /></label>
          <label>Баннер<input maxLength={48} value={bannerId} onChange={(event) => setBannerId(event.target.value)} /></label>
          <label>
            URL аватарки
            <input value={avatarURL} onChange={(event) => setAvatarURL(event.target.value)} placeholder="https://..." />
          </label>
          <label>
            <ShieldAlert size={16} />
            <span>Оповещения об атаках</span>
            <input checked={attackAlerts} onChange={(event) => setAttackAlerts(event.target.checked)} type="checkbox" />
          </label>
          <label>
            <Bell size={16} />
            <span>Готовность производства</span>
            <input checked={productionReady} onChange={(event) => setProductionReady(event.target.checked)} type="checkbox" />
          </label>
          <label>
            <Bell size={16} />
            <span>Рынок</span>
            <input checked={marketUpdates} onChange={(event) => setMarketUpdates(event.target.checked)} type="checkbox" />
          </label>
          <label>
            <MonitorCog size={16} />
            <span>Качество рендера</span>
            <select onChange={(event) => setQuality(event.target.value as RenderQuality)} value={quality}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <button type="button" onClick={saveSettings} disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
          {saveError ? <p role="alert">{saveError}</p> : null}
        </div>
      </Modal>
    </>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(value))
}
