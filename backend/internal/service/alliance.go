package service

import (
	"context"
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
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
}

func NewAllianceService(repo AllianceRepository, economyService *EconomyService, log *slog.Logger) *AllianceService {
	return &AllianceService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }}
}

type AllianceProfile struct {
	Alliance alliance.Alliance
	Self     alliance.Membership
	Members  []alliance.Membership
	Invites  []alliance.Invite
	Treasury []alliance.TreasuryEntry
	Buffs    []alliance.Buff
	Aid      []alliance.TerritoryAid
}

func (s *AllianceService) Profile(ctx context.Context, playerID player.ID) (AllianceProfile, error) {
	item, self, err := s.repo.FindByPlayer(ctx, playerID)
	if err != nil {
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
	return AllianceProfile{Alliance: item, Self: self, Members: members, Invites: invites, Treasury: treasury, Buffs: buffs, Aid: aid}, nil
}

func (s *AllianceService) Create(ctx context.Context, playerID player.ID, name string) (AllianceProfile, error) {
	name = alliance.NormalizeName(name)
	if len([]rune(name)) < 3 || len([]rune(name)) > 32 {
		return AllianceProfile{}, apperror.WithFields(apperror.Validation, "invalid alliance name", map[string]string{"name": "must be 3-32 characters"})
	}
	if _, _, err := s.repo.FindByPlayer(ctx, playerID); err == nil {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "player already has alliance")
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

func (s *AllianceService) Invite(ctx context.Context, actorID, inviteeID player.ID) (alliance.Invite, error) {
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

func (s *AllianceService) RespondInvite(ctx context.Context, playerID player.ID, inviteID alliance.InviteID, accept bool) (AllianceProfile, error) {
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

func (s *AllianceService) SetRole(ctx context.Context, actorID, targetID player.ID, role alliance.Role, treasurer bool) (AllianceProfile, error) {
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
	if role == alliance.RoleLeader {
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

func (s *AllianceService) Donate(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int) (AllianceProfile, error) {
	if amount <= 0 {
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

func (s *AllianceService) UpgradeBuff(ctx context.Context, playerID player.ID, buffID alliance.BuffID) (AllianceProfile, error) {
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
	if level > 5 {
		return AllianceProfile{}, apperror.New(apperror.Conflict, "buff cap reached")
	}
	buff := alliance.Buff{AllianceID: item.ID, ID: buffID, Level: level, UpdatedAt: s.now()}
	if err := s.repo.SaveBuff(ctx, buff); err != nil {
		return AllianceProfile{}, err
	}
	s.log.Info("alliance.buff.upgraded", "event", "alliance.buff.upgraded", "alliance_id", item.ID, "player_id", playerID, "buff_id", buffID, "level", level)
	return s.Profile(ctx, playerID)
}

func (s *AllianceService) AddTerritoryAid(ctx context.Context, playerID player.ID, targetType, targetID string) (alliance.TerritoryAid, error) {
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
