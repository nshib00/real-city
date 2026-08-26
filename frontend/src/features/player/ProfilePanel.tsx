import { Bell, LogOut, MonitorCog, ShieldAlert } from 'lucide-react'
import { useState } from 'react'

import { logout, updateMe } from '../auth/api'
import type { RenderQuality } from '../auth/types'
import { useAuthStore } from '../auth/useAuthStore'

export function ProfilePanel() {
  const { player, setPlayer } = useAuthStore()
  const [quality, setQuality] = useState<RenderQuality>(player?.profile.settings.render_quality ?? 'medium')
  const [raidAlerts, setRaidAlerts] = useState(player?.profile.settings.notifications.raid_alerts ?? true)
  const [productionReady, setProductionReady] = useState(player?.profile.settings.notifications.production_ready ?? true)

  if (!player) {
    return null
  }

  async function saveSettings() {
    if (!player) {
      return
    }
    const updated = await updateMe({
      display_name: player.profile.display_name,
      avatar_url: player.profile.avatar_url,
      settings: {
        notifications: {
          raid_alerts: raidAlerts,
          production_ready: productionReady,
          market_updates: player.profile.settings.notifications.market_updates,
        },
        render_quality: quality,
      },
    })
    setPlayer(updated)
  }

  async function onLogout() {
    await logout()
    setPlayer(null)
  }

  return (
    <section className="profile-panel" aria-label="Профиль игрока">
      <div className="profile-avatar" aria-hidden="true">
        {player.profile.display_name.slice(0, 1).toUpperCase()}
      </div>
      <div className="profile-main">
        <strong>{player.profile.display_name}</strong>
        <span>{player.email}</span>
      </div>
      <label className="profile-toggle">
        <ShieldAlert size={16} />
        <input checked={raidAlerts} onChange={(event) => setRaidAlerts(event.target.checked)} type="checkbox" />
      </label>
      <label className="profile-toggle">
        <Bell size={16} />
        <input checked={productionReady} onChange={(event) => setProductionReady(event.target.checked)} type="checkbox" />
      </label>
      <label className="profile-quality">
        <MonitorCog size={16} />
        <select onChange={(event) => setQuality(event.target.value as RenderQuality)} value={quality}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <button className="icon-button" onClick={saveSettings} title="Сохранить настройки" type="button">
        OK
      </button>
      <button className="icon-button" onClick={onLogout} title="Выйти" type="button">
        <LogOut size={18} />
      </button>
    </section>
  )
}
