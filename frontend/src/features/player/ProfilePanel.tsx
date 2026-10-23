import { Bell, LogOut, MonitorCog, Settings, ShieldAlert, Star, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'

import { getMe, logout, updateMe } from '../auth/api'
import type { RenderQuality } from '../auth/types'
import { useAuthStore } from '../auth/useAuthStore'
import { Drawer } from '../../shared/ui/Drawer'

const levelThresholds = [0, 200, 700, 1900, 4700, 11200, 26200, 61200, 141200, 321200, 721200, 1621200, 3621200, 8121200, 18121200]

export function ProfilePanel() {
  const { player, setPlayer } = useAuthStore()
  const [profileOpen, setProfileOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [cityName, setCityName] = useState('')
  const [avatarURL, setAvatarURL] = useState('')
  const [quality, setQuality] = useState<RenderQuality>('medium')
  const [raidAlerts, setRaidAlerts] = useState(true)
  const [productionReady, setProductionReady] = useState(true)
  const [marketUpdates, setMarketUpdates] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!player?.id) {
      return
    }
    const timer = window.setInterval(() => {
      getMe().then(setPlayer).catch(() => undefined)
    }, 10_000)
    return () => window.clearInterval(timer)
  }, [player?.id, setPlayer])

  useEffect(() => {
    if (!player) {
      return
    }
    setDisplayName(player.profile.display_name)
    setCityName(player.profile.city_name)
    setAvatarURL(player.profile.avatar_url)
    setQuality(player.profile.settings.render_quality)
    setRaidAlerts(player.profile.settings.notifications.raid_alerts)
    setProductionReady(player.profile.settings.notifications.production_ready)
    setMarketUpdates(player.profile.settings.notifications.market_updates)
  }, [player])

  if (!player) {
    return null
  }

  async function saveSettings() {
    if (!player || saving) {
      return
    }
    setSaving(true)
    try {
      const updated = await updateMe({
        display_name: displayName,
        city_name: cityName,
        avatar_url: avatarURL,
        settings: {
          notifications: {
            raid_alerts: raidAlerts,
            production_ready: productionReady,
            market_updates: marketUpdates,
          },
          render_quality: quality,
        },
      })
      setPlayer(updated)
      setSettingsOpen(false)
      setProfileOpen(true)
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
  const xpPercent = nextLevelXP > 0 ? Math.max(0, Math.min(100, Math.round((levelXP / nextLevelXP) * 100))) : 0
  const xpLabel = nextLevelXP > 0 ? `${levelXP}/${nextLevelXP}` : `${levelXP}`

  return (
    <>
      <button className="profile-panel" aria-label="Открыть профиль игрока" onClick={() => setProfileOpen(true)} type="button">
        <span className="profile-avatar-stack">
          <span className="profile-avatar" aria-hidden="true">
            {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : avatarLabel}
          </span>
          <span className="profile-level-badge" title={`Уровень ${level}`}>
            <Star size={12} /> {level}
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

      <Drawer title="Профиль" open={profileOpen} side="left" onClose={() => setProfileOpen(false)}>
        <div className="profile-drawer-body">
          <div className="profile-identity">
            <span className="profile-avatar profile-avatar-large" aria-hidden="true">
              {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : avatarLabel}
            </span>
            <div>
              <strong>{profile.display_name}</strong>
              <span>{profile.city_name}</span>
            </div>
          </div>

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
      </Drawer>

      <Drawer title="Настройки профиля" open={settingsOpen} side="left" onClose={() => setSettingsOpen(false)}>
        <div className="profile-settings-form">
          <label>
            Имя пользователя
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
          </label>
          <label>
            Название города
            <input value={cityName} onChange={(event) => setCityName(event.target.value)} />
          </label>
          <label>
            URL аватарки
            <input value={avatarURL} onChange={(event) => setAvatarURL(event.target.value)} placeholder="https://..." />
          </label>
          <label>
            <ShieldAlert size={16} />
            <span>Оповещения о рейдах</span>
            <input checked={raidAlerts} onChange={(event) => setRaidAlerts(event.target.checked)} type="checkbox" />
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
        </div>
      </Drawer>
    </>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(value))
}
