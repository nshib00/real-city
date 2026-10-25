import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Coins, Gauge, Hammer, Shield } from 'lucide-react'
import type { FormEvent } from 'react'
import { useEffect, useRef, useState } from 'react'

import { playUiSound } from '../../audio/playUiSound'
import { useGameStore } from '../../game/state/useGameStore'
import { Drawer, IconButton } from '../../shared/ui'
import { cancelMarketOrder, createAlliance, createMarketOrder, donateToAlliance, getAllianceProfile, inviteToAlliance, listMarketOrders, respondToAllianceInvite, upgradeAllianceBuff } from '../../shared/api/social'
import { useAuthStore } from '../auth/useAuthStore'
import { ResourceIcon } from '../resources/ResourceIcon'

const buffCatalog = [
  { id: 'build_speed', icon: Hammer, name: 'Быстрая стройка', effect: '+3% к скорости за уровень' },
  { id: 'defense', icon: Shield, name: 'Общая защита', effect: '+2% к прочности за уровень' },
  { id: 'logistics', icon: Gauge, name: 'Логистика', effect: '+2% к доставке за уровень' },
] as const

export function AlliancePanel() {
  const open = useGameStore((state) => state.uiPreferences.alliancePanelOpen)
  const setAlliancePanelOpen = useGameStore((state) => state.setAlliancePanelOpen)
  const queryClient = useQueryClient()
  const profileQuery = useQuery({ queryKey: ['alliances', 'me'], queryFn: getAllianceProfile, enabled: open, refetchInterval: open ? 10_000 : false })
  const marketQuery = useQuery({ queryKey: ['market', 'orders'], queryFn: listMarketOrders, enabled: open })
  const [name, setName] = useState('Северный караван')
  const [invitee, setInvitee] = useState('')
  const playerId = useAuthStore((state) => state.player?.id)
  const seenInvites = useRef<Set<string> | null>(null)
  const [donation, setDonation] = useState({ resource: 'wood', amount: 25 })
  const [order, setOrder] = useState<{ side: 'sell' | 'buy'; resource: string; amount: number; price: number }>({ side: 'sell', resource: 'wood', amount: 50, price: 120 })
  const profile = profileQuery.data?.profile

  const refreshSocial = () => {
    void queryClient.invalidateQueries({ queryKey: ['alliances', 'me'] })
    void queryClient.invalidateQueries({ queryKey: ['market', 'orders'] })
    void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
  }
  const createMutation = useMutation({ mutationFn: createAlliance, onSuccess: refreshSocial })
  const donateMutation = useMutation({ mutationFn: donateToAlliance, onSuccess: () => { playUiSound('social.alliance.treasury'); refreshSocial() } })
  const inviteMutation = useMutation({ mutationFn: inviteToAlliance, onSuccess: () => { playUiSound('social.alliance.invite'); setInvitee(''); refreshSocial() } })
  const respondMutation = useMutation({ mutationFn: ({ id, accept }: { id: string; accept: boolean }) => respondToAllianceInvite(id, accept), onSuccess: (_result, variables) => { playUiSound(variables.accept ? 'social.alliance.accepted' : 'social.alliance.declined'); refreshSocial() } })
  const buffMutation = useMutation({ mutationFn: upgradeAllianceBuff, onSuccess: refreshSocial })
  const marketMutation = useMutation({ mutationFn: createMarketOrder, onSuccess: () => { playUiSound('economy.market.listed'); refreshSocial() } })
  const cancelMarketMutation = useMutation({ mutationFn: cancelMarketOrder, onSuccess: () => { playUiSound('economy.market.cancelled'); refreshSocial() } })

  useEffect(() => {
    const invites = profileQuery.data?.profile.invites
    if (!invites) return
    if (!seenInvites.current) { seenInvites.current = new Set(invites.map((invite) => invite.id)); return }
    if (invites.some((invite) => invite.invitee_id === playerId && invite.status === 'pending' && !seenInvites.current?.has(invite.id))) playUiSound('social.alliance.invite')
    for (const invite of invites) seenInvites.current.add(invite.id)
  }, [profileQuery.data, playerId])

  function submitAlliance(event: FormEvent) {
    event.preventDefault()
    createMutation.mutate(name)
  }

  function submitDonation(event: FormEvent) {
    event.preventDefault()
    donateMutation.mutate(donation)
  }

  function submitOrder(event: FormEvent) {
    event.preventDefault()
    marketMutation.mutate(order)
  }

  return (
    <Drawer title="Союзный дом" open={open} onClose={() => setAlliancePanelOpen(false)}>
      {!profile?.alliance ? (
        <>
        {profile?.invites.filter((invite) => invite.invitee_id === playerId && invite.status === 'pending').map((invite) => (
          <div key={invite.id} className="social-form">
            <span>Приглашение в союз {invite.alliance_id}</span>
            <button type="button" disabled={respondMutation.isPending} onClick={() => respondMutation.mutate({ id: invite.id, accept: true })}>Принять</button>
            <button type="button" disabled={respondMutation.isPending} onClick={() => respondMutation.mutate({ id: invite.id, accept: false })}>Отклонить</button>
          </div>
        ))}
        <form className="social-form" onSubmit={submitAlliance}>
          <label>
            <span>Название союза</span>
            <input value={name} minLength={3} maxLength={32} onChange={(event) => setName(event.target.value)} />
          </label>
          <button type="submit" disabled={createMutation.isPending}>Создать союз</button>
        </form>
        </>
      ) : (
        <>
          <section className="alliance-summary">
            <strong>{profile.alliance.name}</strong>
            <span>Уровень дома {profile.alliance.level}</span>
            <span>Участники {profile.members.length}/{profile.alliance.member_limit}</span>
            <span>{roleLabel(profile.self?.role)}{profile.self?.treasurer ? ', казначей' : ''}</span>
          </section>
          <form className="social-form alliance-treasury" onSubmit={submitDonation}>
            <h3>Казна</h3>
            <label>
              <span>Ресурс</span>
              <select value={donation.resource} onChange={(event) => setDonation({ ...donation, resource: event.target.value })}>
                <option value="wood">Древесина</option>
                <option value="stone">Камень</option>
                <option value="coins">Монеты</option>
                <option value="fuel">Бензин</option>
              </select>
            </label>
            <label>
              <span>Количество</span>
              <input type="number" min={1} value={donation.amount} onChange={(event) => setDonation({ ...donation, amount: Number(event.target.value) })} />
            </label>
            <button type="submit" disabled={donateMutation.isPending}>Пожертвовать</button>
            {profile.treasury.slice(0, 4).map((entry) => (
              <p key={entry.id}>
                <ResourceIcon id={entry.resource} label={entry.resource} /> {entry.amount} от {entry.player_id}
              </p>
            ))}
          </form>
          <section className="alliance-list">
            <h3>Иерархия</h3>
            {profile.self && ['leader', 'deputy', 'officer'].includes(profile.self.role) ? (
              <form className="social-form" onSubmit={(event) => { event.preventDefault(); if (invitee.trim()) inviteMutation.mutate(invitee.trim()) }}>
                <input aria-label="ID игрока для приглашения" value={invitee} onChange={(event) => setInvitee(event.target.value)} />
                <button type="submit" disabled={inviteMutation.isPending}>Пригласить</button>
              </form>
            ) : null}
            {profile.members.map((member) => (
              <p key={member.player_id}>
                <strong>{roleLabel(member.role)}{member.treasurer ? ' / казначей' : ''}</strong>
                <span>{member.player_id}</span>
              </p>
            ))}
          </section>
          <section className="alliance-buffs">
            <h3>Баффы</h3>
            {buffCatalog.map((buff) => {
              const level = profile.buffs.find((item) => item.id === buff.id)?.level ?? 0
              return (
                <article key={buff.id}>
                  <IconButton label={buff.name} icon={buff.icon} onClick={() => buffMutation.mutate(buff.id)} />
                  <strong>{buff.name}</strong>
                  <span>ур. {level}</span>
                  <small>{buff.effect}</small>
                </article>
              )
            })}
          </section>
        </>
      )}
      <form className="social-form market-panel" onSubmit={submitOrder}>
        <h3>Рынок</h3>
        <select value={order.side} onChange={(event) => setOrder({ ...order, side: event.target.value as 'sell' | 'buy' })}>
          <option value="sell">Продажа</option>
          <option value="buy">Покупка</option>
        </select>
        <select value={order.resource} onChange={(event) => setOrder({ ...order, resource: event.target.value })}>
          <option value="wood">Древесина</option>
          <option value="stone">Камень</option>
          <option value="brick">Кирпич</option>
          <option value="fuel">Бензин</option>
        </select>
        <input aria-label="Количество в ордере" type="number" min={1} value={order.amount} onChange={(event) => setOrder({ ...order, amount: Number(event.target.value) })} />
        <input aria-label="Цена ордера" type="number" min={1} value={order.price} onChange={(event) => setOrder({ ...order, price: Number(event.target.value) })} />
        <button type="submit" disabled={marketMutation.isPending}>Выставить</button>
        {marketQuery.data?.orders.slice(0, 5).map((item) => (
          <p key={item.id}>
            <strong>{item.side === 'sell' ? 'Продажа' : 'Покупка'}</strong>
            <ResourceIcon id={item.resource} label={item.resource} /> {item.amount} за {item.price} монет
            {item.status === 'open' ? <button type="button" disabled={cancelMarketMutation.isPending} onClick={() => cancelMarketMutation.mutate(item.id)}>Отменить ордер</button> : null}
          </p>
        ))}
      </form>
      {(profileQuery.isError || createMutation.isError || donateMutation.isError || inviteMutation.isError || respondMutation.isError || marketMutation.isError) ? <p className="build-error">Социальный API временно недоступен.</p> : null}
      <section className="alliance-treasury">
        <p><Coins size={16} aria-hidden="true" /> Комиссия рынка резервируется сразу, пожертвования списываются из инвентаря.</p>
      </section>
    </Drawer>
  )
}

function roleLabel(role?: string) {
  switch (role) {
    case 'leader':
      return 'Лидер'
    case 'deputy':
      return 'Заместитель'
    case 'officer':
      return 'Офицер'
    case 'member':
      return 'Участник'
    default:
      return 'Без союза'
  }
}
