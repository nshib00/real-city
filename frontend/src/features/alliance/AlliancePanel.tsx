import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Coins, Gauge, Hammer, Shield } from '../../shared/ui/icons'
import type { FormEvent } from 'react'
import { useEffect, useRef, useState } from 'react'

import { allianceBuffCatalog } from '../../../../shared/catalog/alliance-buffs'
import { resourceCatalog } from '../../../../shared/catalog/resources'
import { playUiSound } from '../../audio/playUiSound'
import { useGameStore } from '../../game/state/useGameStore'
import { Drawer, IconButton } from '../../shared/ui'
import { spendAllianceTreasury, transferAllianceLeadership, leaveAlliance, kickAllianceMember, cancelMarketOrder, createAlliance, createMarketOrder, donateToAlliance, getAllianceProfile, inviteToAlliance, listMarketOrders, respondToAllianceInvite, upgradeAllianceBuff } from '../../shared/api/social'
import { useAuthStore } from '../auth/useAuthStore'
import { ResourceIcon } from '../resources/ResourceIcon'
import { PlayerName } from '../player/PlayerName'

const buffCatalog = allianceBuffCatalog.map((buff) => ({ ...buff, icon: buff.id === 'build_speed' || buff.id === 'repair_speed' ? Hammer : buff.id === 'defense' ? Shield : Gauge }))


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
  const [withdrawal, setWithdrawal] = useState({ resource: 'wood', amount: 1, recipient: '' })
  const [order, setOrder] = useState<{ side: 'sell' | 'buy'; resource: string; amount: number; price: number }>({ side: 'sell', resource: 'wood', amount: 50, price: 120 })
  const profile = profileQuery.data?.profile

  const refreshSocial = () => {
    void queryClient.invalidateQueries({ queryKey: ['alliances', 'me'] })
    void queryClient.invalidateQueries({ queryKey: ['market', 'orders'] })
    void queryClient.invalidateQueries({ queryKey: ['economy', 'inventory'] })
  }
  const transferMutation = useMutation({ mutationFn: transferAllianceLeadership, onSuccess: refreshSocial })
  const leaveMutation = useMutation({ mutationFn: leaveAlliance, onSuccess: refreshSocial })
  const kickMutation = useMutation({ mutationFn: kickAllianceMember, onSuccess: refreshSocial })
  const membershipError = leaveMutation.error ?? kickMutation.error ?? transferMutation.error
  const createMutation = useMutation({ mutationFn: createAlliance, onSuccess: refreshSocial })
  const spendMutation = useMutation({ mutationFn: spendAllianceTreasury, onSuccess: refreshSocial })
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
      <p className="panel-note">Участники, казна и полномочия вашего союза. Действия доступны согласно вашей роли.</p>
      {profileQuery.isPending ? <p role="status">Загружаем сведения о союзе…</p> : null}
      {profileQuery.error ? <p role="alert">Не удалось загрузить союз. <button type="button" onClick={() => void profileQuery.refetch()}>Повторить</button></p> : null}
      {profileQuery.data && !profile?.alliance ? (
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
      ) : profile?.alliance ? (
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
                <ResourceIcon id={entry.resource} label={entry.resource} /> {entry.amount} от <PlayerName playerId={entry.player_id} />
              </p>
            ))}
          </form>
          <section className="alliance-list">
            <h3>Иерархия</h3>
            <button type="button" disabled={leaveMutation.isPending} onClick={() => leaveMutation.mutate()}>Выйти из союза</button>
            {membershipError ? <p role="alert">{membershipError.message}</p> : null}
            {profile.self && ['leader', 'deputy', 'officer'].includes(profile.self.role) ? (
              <form className="social-form" onSubmit={(event) => { event.preventDefault(); if (invitee.trim()) inviteMutation.mutate(invitee.trim()) }}>
                <input aria-label="ID игрока для приглашения" value={invitee} onChange={(event) => setInvitee(event.target.value)} />
                <button type="submit" disabled={inviteMutation.isPending}>Пригласить</button>
              </form>
            ) : null}
            {profile.members.map((member) => (
              <p key={member.player_id}>
                <strong>{roleLabel(member.role)}{member.treasurer ? ' / казначей' : ''}</strong>
                <span><PlayerName playerId={member.player_id} /></span>
                {profile.self?.role === 'leader' && member.player_id !== playerId ? <button type="button" disabled={transferMutation.isPending} onClick={() => transferMutation.mutate(member.player_id)}>Передать лидерство</button> : null}
                {profile.self && member.player_id !== playerId && roleRank(profile.self.role) > roleRank(member.role) ? <button type="button" disabled={kickMutation.isPending} onClick={() => kickMutation.mutate(member.player_id)}>Исключить</button> : null}
              </p>
            ))}
          </section>
          <section className="alliance-treasury-spend">
            <h3>Баланс казны</h3>
            {Object.entries(profile.balance ?? {}).map(([id, amount]) => <span key={id}><ResourceIcon id={id} label={resourceCatalog.find(r => r.id === id)?.name ?? id} />{amount} </span>)}
            {profile.self?.role === 'leader' || profile.self?.treasurer ? <form className="social-form" onSubmit={(event) => { event.preventDefault(); spendMutation.mutate(withdrawal) }}>
              <label>Ресурс<select value={withdrawal.resource} onChange={e => setWithdrawal({ ...withdrawal, resource: e.target.value })}>{resourceCatalog.filter(r => r.id !== 'population').map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>
              <label>Количество<input type="number" min={1} max={2147483647} value={withdrawal.amount} onChange={e => setWithdrawal({ ...withdrawal, amount: Number(e.target.value) })} /></label>
              <label>Получатель<select required value={withdrawal.recipient} onChange={e => setWithdrawal({ ...withdrawal, recipient: e.target.value })}><option value="">Выберите участника</option>{profile.members.map(m => <option key={m.player_id} value={m.player_id}><PlayerName playerId={m.player_id} /></option>)}</select></label>
              <button type="submit" disabled={spendMutation.isPending}>Выдать из казны</button>
              {spendMutation.error ? <p role="alert">{spendMutation.error.message}</p> : null}
            </form> : null}
          </section>
          <section className="alliance-buffs">
            <h3>Баффы</h3>
            {buffMutation.error ? <p role="alert">{buffMutation.error.message}</p> : null}
            {buffCatalog.map((buff) => {
              const level = profile.buffs.find((item) => item.id === buff.id)?.level ?? 0
              return (
                <article key={buff.id}>
                  <IconButton label={buff.name} icon={buff.icon} disabled={buffMutation.isPending || level >= buff.max_level || !(profile.self?.role === 'leader' || profile.self?.treasurer) || (profile.balance?.[buff.resource] ?? 0) < buff.base_cost * (level + 1) ** 2} onClick={() => buffMutation.mutate(buff.id)} />
                  <strong>{buff.name}</strong>
                  <span>ур. {level}</span>
                  <small>{buff.id === 'defense' ? 'Снижение урона' : buff.id === 'logistics' ? 'Добыча' : 'Ускорение'}: {buff.percent * level}%</small>
                  <small>{level >= buff.max_level ? 'Максимальный уровень' : `Следующий уровень: ${buff.base_cost * (level + 1) ** 2} ${resourceCatalog.find(r => r.id === buff.resource)?.name ?? ''}`}</small>
                </article>
              )
            })}
          </section>
        </>
      ) : null}
      <form className="social-form market-panel" onSubmit={submitOrder}>
        <h3>Рынок</h3>
        {marketQuery.error ? <p role="alert">Рынок не загружен. <button type="button" onClick={() => void marketQuery.refetch()}>Повторить</button></p> : null}
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
            {item.filled_amount ? <span> Выполнено: {item.filled_amount} из {item.amount}.</span> : null}
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

function roleRank(role: string) { return ({ member: 0, officer: 1, deputy: 2, leader: 3 } as Record<string, number>)[role] ?? -1 }
