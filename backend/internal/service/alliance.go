package service

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type AllianceService struct {
	repo    AllianceRepository
	uow     UnitOfWork
	events  *EventBus
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
}

func NewAllianceService(repo AllianceRepository, economyService *EconomyService, log *slog.Logger) *AllianceService {
	return &AllianceService{repo: repo, economy: economyService, uow: snapshotUnitOfWork{[]any{repo, economyService.repo}}, log: log, now: func() time.Time { return time.Now().UTC() }}
}

type AllianceProfile struct {
	Alliance alliance.Alliance
	Self     alliance.Membership
	Members  []alliance.Membership
	Invites  []alliance.Invite
	Treasury []alliance.TreasuryEntry
	Balance  map[economy.ResourceType]int
	Buffs    []alliance.Buff
	Aid      []alliance.TerritoryAid
}

func (s *AllianceService) Profile(ctx context.Context, playerID player.ID) (AllianceProfile, error) {
	item, self, err := s.repo.FindByPlayer(ctx, playerID)
	if err != nil {
		if !isNotFound(err) {
			return AllianceProfile{}, err
		}
		invites, inviteErr := s.repo.ListInvitesForPlayer(ctx, playerID)
		if inviteErr != nil {
			return AllianceProfile{}, inviteErr
		}
		return AllianceProfile{Invites: invites}, nil
	}
	members, err := s.repo.ListMembers(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	treasury, err := s.repo.ListTreasury(ctx, item.ID, 30)
	if err != nil {
		return AllianceProfile{}, err
	}
	buffs, err := s.repo.ListBuffs(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	aid, err := s.repo.ListTerritoryAid(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	invites, err := s.repo.ListInvitesForPlayer(ctx, playerID)
	if err != nil {
		return AllianceProfile{}, err
	}
	balance, err := s.repo.TreasuryBalance(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	return AllianceProfile{Balance: balance, Alliance: item, Self: self, Members: members, Invites: invites, Treasury: treasury, Buffs: buffs, Aid: aid}, nil
}

func (s *AllianceService) create(ctx context.Context, playerID player.ID, name string) (AllianceProfile, error) {
	name = alliance.NormalizeName(name)
	if len([]rune(name)) < 3 || len([]rune(name)) > 32 {
		return AllianceProfile{}, apperror.WithFields(apperror.Validation, "invalid alliance name", map[string]string{"name": "must be 3-32 characters"})
	}
	if _, _, err := s.repo.FindByPlayer(ctx, playerID); err == nil {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "player already has alliance")
	} else if !isNotFound(err) {
		return AllianceProfile{}, err
	}
	now := s.now()
	item := alliance.Alliance{ID: alliance.ID(fmt.Sprintf("alliance_%d", now.UnixNano())), Name: name, LeaderID: playerID, Level: 1, CreatedAt: now, UpdatedAt: now}
	if err := s.repo.Create(ctx, item); err != nil {
		return AllianceProfile{}, err
	}
	if err := s.repo.SaveMembership(ctx, alliance.Membership{AllianceID: item.ID, PlayerID: playerID, Role: alliance.RoleLeader, JoinedAt: now}); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.created", "event", "alliance.created", "alliance_id", item.ID, "player_id", playerID)
	return s.Profile(ctx, playerID)
}

func (s *AllianceService) invite(ctx context.Context, actorID, inviteeID player.ID) (alliance.Invite, error) {
	item, actor, err := s.repo.FindByPlayer(ctx, actorID)
	if err != nil {
		return alliance.Invite{}, err
	}
	if !alliance.CanManageMembers(actor.Role) {
		return alliance.Invite{}, apperror.New(apperror.Forbidden, "not allowed to invite members")
	}
	now := s.now()
	invite := alliance.Invite{ID: alliance.InviteID(fmt.Sprintf("invite_%d", now.UnixNano())), AllianceID: item.ID, InviterID: actorID, InviteeID: inviteeID, Status: alliance.InvitePending, CreatedAt: now}
	if err := s.repo.CreateInvite(ctx, invite); err != nil {
		return alliance.Invite{}, err
	}
	s.log.Info("alliance.invite.created", "event", "alliance.invite.created", "alliance_id", item.ID, "inviter_id", actorID, "invitee_id", inviteeID)
	return invite, nil
}

func (s *AllianceService) respondInvite(ctx context.Context, playerID player.ID, inviteID alliance.InviteID, accept bool) (AllianceProfile, error) {
	invite, err := s.repo.FindInvite(ctx, inviteID)
	if err != nil {
		return AllianceProfile{}, err
	}
	if invite.InviteeID != playerID {
		return AllianceProfile{}, apperror.New(apperror.Forbidden, "invite belongs to another player")
	}
	if invite.Status != alliance.InvitePending {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "invite already answered")
	}
	now := s.now()
	invite.RespondedAt = &now
	if !accept {
		invite.Status = alliance.InviteDeclined
		if err := s.repo.UpdateInvite(ctx, invite); err != nil {
			return AllianceProfile{}, err
		}
		s.log.Info("alliance.invite.declined", "event", "alliance.invite.declined", "alliance_id", invite.AllianceID, "player_id", playerID)
		return s.Profile(ctx, playerID)
	}
	if _, _, err := s.repo.FindByPlayer(ctx, playerID); err == nil {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "player already has alliance")
	} else if !isNotFound(err) {
		return AllianceProfile{}, err
	}
	item, err := s.repo.FindByID(ctx, invite.AllianceID)
	if err != nil {
		return AllianceProfile{}, err
	}
	members, err := s.repo.ListMembers(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	if len(members) >= alliance.MemberLimit(item.Level) {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "alliance member limit reached")
	}
	invite.Status = alliance.InviteAccepted
	if err := s.repo.UpdateInvite(ctx, invite); err != nil {
		return AllianceProfile{}, err
	}
	if err := s.repo.SaveMembership(ctx, alliance.Membership{AllianceID: item.ID, PlayerID: playerID, Role: alliance.RoleMember, JoinedAt: now}); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.invite.accepted", "event", "alliance.invite.accepted", "alliance_id", item.ID, "player_id", playerID)
	return s.Profile(ctx, playerID)
}

func (s *AllianceService) setRole(ctx context.Context, actorID, targetID player.ID, role alliance.Role, treasurer bool) (AllianceProfile, error) {
	item, actor, err := s.repo.FindByPlayer(ctx, actorID)
	if err != nil {
		return AllianceProfile{}, err
	}
	if actor.Role != alliance.RoleLeader {
		return AllianceProfile{}, apperror.New(apperror.Forbidden, "only leader can change roles")
	}
	members, err := s.repo.ListMembers(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	deputies := 0
	var target alliance.Membership
	found := false
	for _, member := range members {
		if member.PlayerID == targetID {
			target = member
			found = true
			continue
		}
		if member.Role == alliance.RoleDeputy {
			deputies++
		}
	}
	if !found {
		return AllianceProfile{}, apperror.New(apperror.NotFound, "alliance member not found")
	}
	if target.Role == alliance.RoleLeader || (role != alliance.RoleDeputy && role != alliance.RoleOfficer && role != alliance.RoleMember) {
		return AllianceProfile{}, apperror.New(apperror.Validation, "leader transfer is not part of MVP")
	}
	if role == alliance.RoleDeputy && deputies >= 2 {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "deputy limit reached")
	}
	if treasurer && role != alliance.RoleDeputy {
		return AllianceProfile{}, apperror.New(apperror.Validation, "treasurer must be a deputy")
	}
	target.Role = role
	target.Treasurer = treasurer
	if treasurer {
		for _, member := range members {
			if member.PlayerID != targetID && member.Treasurer {
				member.Treasurer = false
				if err := s.repo.SaveMembership(ctx, member); err != nil {
					return AllianceProfile{}, err
				}
			}
		}
	}
	if err := s.repo.SaveMembership(ctx, target); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.role.changed", "event", "alliance.role.changed", "alliance_id", item.ID, "actor_id", actorID, "target_id", targetID, "role", role, "treasurer", treasurer)
	return s.Profile(ctx, actorID)
}

func (s *AllianceService) donate(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int) (AllianceProfile, error) {
	if amount <= 0 || amount > 2147483647 || resource == economy.ResourcePopulation {
		return AllianceProfile{}, apperror.New(apperror.Validation, "amount must be positive")
	}
	item, _, err := s.repo.FindByPlayer(ctx, playerID)
	if err != nil {
		return AllianceProfile{}, err
	}
	if _, err := s.economy.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: resource, Amount: amount}}, "alliance_treasury_donation"); err != nil {
		return AllianceProfile{}, err
	}
	now := s.now()
	entry := alliance.TreasuryEntry{ID: alliance.LedgerID(fmt.Sprintf("ledger_%d", now.UnixNano())), AllianceID: item.ID, PlayerID: playerID, Kind: alliance.LedgerDonation, Resource: resource, Amount: amount, Description: "donation", CreatedAt: now}
	if err := s.repo.AddTreasuryEntry(ctx, entry); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.treasury.donated", "event", "alliance.treasury.donated", "alliance_id", item.ID, "player_id", playerID, "resource", resource, "amount", amount)
	return s.Profile(ctx, playerID)
}

func (s *AllianceService) upgradeBuff(ctx context.Context, playerID player.ID, buffID alliance.BuffID) (AllianceProfile, error) {
	item, member, err := s.repo.FindByPlayer(ctx, playerID)
	if err != nil {
		return AllianceProfile{}, err
	}
	if !alliance.CanSpendTreasury(member) {
		return AllianceProfile{}, apperror.New(apperror.Forbidden, "not allowed to spend treasury")
	}
	buffs, err := s.repo.ListBuffs(ctx, item.ID)
	if err != nil {
		return AllianceProfile{}, err
	}
	level := 1
	for _, buff := range buffs {
		if buff.ID == buffID {
			level = buff.Level + 1
			break
		}
	}
	spec, known := alliance.BuffSpec(buffID)
	if !known {
		return AllianceProfile{}, apperror.New(apperror.Validation, "Неизвестное усиление союза")
	}
	if level > spec.MaxLevel {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "buff cap reached")
	}
	if err := s.debitTreasury(ctx, item.ID, playerID, economy.ResourceType(spec.Resource), spec.BaseCost*level*level, "buff:"+string(buffID)); err != nil {
		return AllianceProfile{}, err
	}
	buff := alliance.Buff{AllianceID: item.ID, ID: buffID, Level: level, UpdatedAt: s.now()}
	if err := s.repo.SaveBuff(ctx, buff); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.buff.upgraded", "event", "alliance.buff.upgraded", "alliance_id", item.ID, "player_id", playerID, "buff_id", buffID, "level", level)
	return s.Profile(ctx, playerID)
}

func (s *AllianceService) addTerritoryAid(ctx context.Context, playerID player.ID, targetType, targetID string) (alliance.TerritoryAid, error) {
	item, _, err := s.repo.FindByPlayer(ctx, playerID)
	if err != nil {
		return alliance.TerritoryAid{}, err
	}
	aid := alliance.TerritoryAid{AllianceID: item.ID, PlayerID: playerID, TargetType: targetType, TargetID: targetID, CreatedAt: s.now()}
	if err := s.repo.AddTerritoryAid(ctx, aid); err != nil {
		return alliance.TerritoryAid{}, err
	}
	s.log.Info("alliance.territory_aid.added", "event", "alliance.territory_aid.added", "alliance_id", item.ID, "player_id", playerID, "target_type", targetType, "target_id", targetID)
	return aid, nil
}

func (s *AllianceService) Create(ctx context.Context, playerID player.ID, name string) (result AllianceProfile, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {

		var e error
		result, e = s.create(WithoutCatchUp(ctx), playerID, name)
		if e != nil {
			return e
		}
		return s.notify(ctx, playerID, "alliance.created")
	})
	return
}

func (s *AllianceService) Invite(ctx context.Context, actorID, inviteeID player.ID) (result alliance.Invite, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, actorID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		result, e = s.invite(WithoutCatchUp(ctx), actorID, inviteeID)
		if e != nil {
			return e
		}
		return s.notify(ctx, actorID, "alliance.invite.created", inviteeID)
	})
	return
}

func (s *AllianceService) RespondInvite(ctx context.Context, playerID player.ID, inviteID alliance.InviteID, accept bool) (result AllianceProfile, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		inv, e := s.repo.FindInvite(ctx, inviteID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, inv.AllianceID); e != nil {
			return e
		}
		result, e = s.respondInvite(WithoutCatchUp(ctx), playerID, inviteID, accept)
		if e != nil {
			return e
		}
		kind := EventType("alliance.invite.declined")
		if accept {
			kind = "alliance.invite.accepted"
		}
		return s.notify(ctx, playerID, kind, inv.InviterID)
	})
	return
}

func (s *AllianceService) SetRole(ctx context.Context, actorID, targetID player.ID, role alliance.Role, treasurer bool) (result AllianceProfile, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, actorID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		result, e = s.setRole(WithoutCatchUp(ctx), actorID, targetID, role, treasurer)
		if e != nil {
			return e
		}
		return s.notify(ctx, actorID, "alliance.role.changed", targetID)
	})
	return
}

func (s *AllianceService) Donate(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int) (result AllianceProfile, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, playerID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		result, e = s.donate(WithoutCatchUp(ctx), playerID, resource, amount)
		if e != nil {
			return e
		}
		return s.notify(ctx, playerID, "alliance.treasury.donated")
	})
	return
}

func (s *AllianceService) UpgradeBuff(ctx context.Context, playerID player.ID, buffID alliance.BuffID) (result AllianceProfile, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, playerID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		result, e = s.upgradeBuff(WithoutCatchUp(ctx), playerID, buffID)
		if e != nil {
			return e
		}
		return s.notify(ctx, playerID, "alliance.buff.upgraded")
	})
	return
}

func (s *AllianceService) AddTerritoryAid(ctx context.Context, playerID player.ID, targetType, targetID string) (result alliance.TerritoryAid, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, playerID)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		result, e = s.addTerritoryAid(WithoutCatchUp(ctx), playerID, targetType, targetID)
		if e != nil {
			return e
		}
		return s.notify(ctx, playerID, "alliance.territory_aid.added")
	})
	return
}

func (s *AllianceService) SetUnitOfWork(uow UnitOfWork) {
	if uow != nil {
		s.uow = uow
	}
}
func (s *AllianceService) SetEventBus(events *EventBus) { s.events = events }
func isNotFound(err error) bool {
	var e *apperror.Error
	return errors.As(err, &e) && e.Kind == apperror.NotFound
}
func (s *AllianceService) notify(ctx context.Context, actor player.ID, kind EventType, extra ...player.ID) error {
	ids := map[player.ID]bool{actor: true}
	a, _, err := s.repo.FindByPlayer(ctx, actor)
	if err != nil && !isNotFound(err) {
		return err
	}
	if err == nil {
		members, e := s.repo.ListMembers(ctx, a.ID)
		if e != nil {
			return e
		}
		for _, m := range members {
			ids[m.PlayerID] = true
		}
	}
	for _, id := range extra {
		ids[id] = true
	}
	for id := range ids {
		publishEvent(ctx, s.events, Event{Type: kind, PlayerID: id, Payload: map[string]any{"alliance_id": a.ID, "player_id": actor}})
	}
	return nil
}

// A leader must Перед выходом передайте лидерство другому участнику a populated alliance.
// The last leader dissolves the empty alliance and its pending invitations.
func (s *AllianceService) Leave(ctx context.Context, p player.ID) error {
	return s.removeMember(ctx, p, p)
}
func (s *AllianceService) Kick(ctx context.Context, p, target player.ID) error {
	if p == target {
		return apperror.New(apperror.Validation, "Для выхода используйте действие «Выйти из союза»")
	}
	return s.removeMember(ctx, p, target)
}
func (s *AllianceService) removeMember(ctx context.Context, p, target player.ID) error {
	return transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, err := s.repo.FindByPlayer(ctx, p)
		if err != nil {
			return err
		}
		if err = s.repo.LockAlliance(ctx, a.ID); err != nil {
			return err
		}
		a, actor, err := s.repo.FindByPlayer(ctx, p)
		if err != nil {
			return err
		}
		b, victim, err := s.repo.FindByPlayer(ctx, target)
		if err != nil {
			return err
		}
		if a.ID != b.ID {
			return apperror.New(apperror.Forbidden, "target belongs to another alliance")
		}
		members, err := s.repo.ListMembers(ctx, a.ID)
		if err != nil {
			return err
		}
		rank := map[alliance.Role]int{alliance.RoleMember: 0, alliance.RoleOfficer: 1, alliance.RoleDeputy: 2, alliance.RoleLeader: 3}
		if p != target && (!alliance.CanManageMembers(actor.Role) || rank[actor.Role] <= rank[victim.Role]) {
			return apperror.New(apperror.Forbidden, "Нельзя исключить участника с равной или более высокой ролью")
		}
		if victim.Role == alliance.RoleLeader && len(members) > 1 {
			return apperror.New(apperror.Conflict, "Перед выходом передайте лидерство другому участнику")
		}
		if err = s.repo.DeleteMembership(ctx, a.ID, target); err != nil {
			return err
		}
		if victim.Role == alliance.RoleLeader {
			if err = s.repo.DeleteAlliance(ctx, a.ID); err != nil {
				return err
			}
		}
		kind := EventType("alliance.member.left")
		if p != target {
			kind = "alliance.member.kicked"
		}
		for _, m := range members {
			publishEvent(ctx, s.events, Event{Type: kind, PlayerID: m.PlayerID, Payload: map[string]any{"alliance_id": a.ID, "target_player_id": target}})
		}
		s.log.Info(string(kind), "event", kind, "alliance_id", a.ID, "player_id", p, "target_id", target)
		return nil
	})
}

func (s *AllianceService) TransferLeadership(ctx context.Context, p, target player.ID) error {
	if p == target {
		return apperror.New(apperror.Validation, "Выберите другого участника союза")
	}
	return transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, err := s.repo.FindByPlayer(ctx, p)
		if err != nil {
			return err
		}
		if err = s.repo.LockAlliance(ctx, a.ID); err != nil {
			return err
		}
		_, actor, err := s.repo.FindByPlayer(ctx, p)
		if err != nil {
			return err
		}
		if actor.Role != alliance.RoleLeader {
			return apperror.New(apperror.Forbidden, "Передать лидерство может только лидер")
		}
		b, member, err := s.repo.FindByPlayer(ctx, target)
		if err != nil {
			return err
		}
		if a.ID != b.ID {
			return apperror.New(apperror.Forbidden, "target belongs to another alliance")
		}
		actor.Role = alliance.RoleMember
		actor.Treasurer = false
		member.Role = alliance.RoleLeader
		member.Treasurer = false
		if err = s.repo.SaveMembership(ctx, actor); err != nil {
			return err
		}
		if err = s.repo.SaveMembership(ctx, member); err != nil {
			return err
		}
		if err = s.repo.UpdateLeader(ctx, a.ID, target); err != nil {
			return err
		}
		return s.notify(ctx, p, "alliance.leader.changed", target)
	})
}

func (s *AllianceService) debitTreasury(ctx context.Context, id alliance.ID, p player.ID, resource economy.ResourceType, amount int, description string) error {
	balance, err := s.repo.TreasuryBalance(ctx, id)
	if err != nil {
		return err
	}
	if balance[resource] < amount {
		return apperror.New(apperror.Conflict, "В казне недостаточно ресурсов")
	}
	return s.repo.AddTreasuryEntry(ctx, alliance.TreasuryEntry{ID: alliance.LedgerID(fmt.Sprintf("ledger_%d", s.now().UnixNano())), AllianceID: id, PlayerID: p, Kind: alliance.LedgerSpend, Resource: resource, Amount: amount, Description: description, CreatedAt: s.now()})
}
func (s *AllianceService) SpendTreasury(ctx context.Context, p, target player.ID, resource economy.ResourceType, amount int) (result AllianceProfile, err error) {
	if amount <= 0 || amount > 2147483647 || resource == economy.ResourcePopulation {
		return result, apperror.New(apperror.Validation, "Количество должно быть положительным")
	}
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		a, _, e := s.repo.FindByPlayer(ctx, p)
		if e != nil {
			return e
		}
		if e = s.repo.LockAlliance(ctx, a.ID); e != nil {
			return e
		}
		a, actor, e := s.repo.FindByPlayer(ctx, p)
		if e != nil {
			return e
		}
		if !alliance.CanSpendTreasury(actor) {
			return apperror.New(apperror.Forbidden, "Расходовать казну может лидер или казначей")
		}
		b, _, e := s.repo.FindByPlayer(ctx, target)
		if e != nil {
			return e
		}
		if a.ID != b.ID {
			return apperror.New(apperror.Forbidden, "Получатель должен состоять в вашем союзе")
		}
		if e = s.debitTreasury(ctx, a.ID, p, resource, amount, "withdrawal:"+string(target)); e != nil {
			return e
		}
		if _, overflow, e := s.economy.Add(WithoutCatchUp(ctx), target, []economy.ResourceAmount{{Resource: resource, Amount: amount}}, "alliance:withdrawal"); e != nil {
			return e
		} else if len(overflow) > 0 {
			return apperror.New(apperror.Conflict, "Хранилище получателя заполнено")
		}
		if e = s.notify(ctx, p, "alliance.treasury.spent", target); e != nil {
			return e
		}
		result, e = s.Profile(ctx, p)
		return e
	})
	return
}

// The strongest buff for a mechanic applies once; unsupported legacy ids have no effect.
func (s *AllianceService) Percent(ctx context.Context, p player.ID, effect string) (int, error) {
	a, _, err := s.repo.FindByPlayer(ctx, p)
	if isNotFound(err) {
		return 0, nil
	}
	if err != nil {
		return 0, err
	}
	buffs, err := s.repo.ListBuffs(ctx, a.ID)
	if err != nil {
		return 0, err
	}
	percent := 0
	for _, b := range buffs {
		spec, ok := alliance.BuffSpec(b.ID)
		if ok && spec.Effect == effect {
			percent = max(percent, spec.Percent*min(max(b.Level, 0), spec.MaxLevel))
		}
	}
	return min(percent, 20), nil
}
