package memory

import (
	"context"
	"sort"
	"sync"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type SocialRepo struct {
	mu          sync.RWMutex
	alliances   map[alliance.ID]alliance.Alliance
	memberships map[alliance.ID]map[player.ID]alliance.Membership
	invites     map[alliance.InviteID]alliance.Invite
	treasury    map[alliance.ID][]alliance.TreasuryEntry
	buffs       map[alliance.ID]map[alliance.BuffID]alliance.Buff
	aid         map[alliance.ID][]alliance.TerritoryAid
	messages    []chat.Message
	orders      map[market.OrderID]market.Order
}

func NewSocialRepo() *SocialRepo {
	return &SocialRepo{
		alliances:   make(map[alliance.ID]alliance.Alliance),
		memberships: make(map[alliance.ID]map[player.ID]alliance.Membership),
		invites:     make(map[alliance.InviteID]alliance.Invite),
		treasury:    make(map[alliance.ID][]alliance.TreasuryEntry),
		buffs:       make(map[alliance.ID]map[alliance.BuffID]alliance.Buff),
		aid:         make(map[alliance.ID][]alliance.TerritoryAid),
		orders:      make(map[market.OrderID]market.Order),
	}
}

func (r *SocialRepo) Create(ctx context.Context, item alliance.Alliance) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.alliances[item.ID]; ok {
		return apperror.New(apperror.Conflict, "alliance already exists")
	}
	r.alliances[item.ID] = item
	return nil
}

func (r *SocialRepo) FindByID(ctx context.Context, id alliance.ID) (alliance.Alliance, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.alliances[id]
	if !ok {
		return alliance.Alliance{}, apperror.New(apperror.NotFound, "alliance not found")
	}
	return item, nil
}

func (r *SocialRepo) FindByPlayer(ctx context.Context, playerID player.ID) (alliance.Alliance, alliance.Membership, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	for allianceID, members := range r.memberships {
		if member, ok := members[playerID]; ok {
			return r.alliances[allianceID], member, nil
		}
	}
	return alliance.Alliance{}, alliance.Membership{}, apperror.New(apperror.NotFound, "alliance membership not found")
}

func (r *SocialRepo) ListMembers(ctx context.Context, id alliance.ID) ([]alliance.Membership, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	members := r.memberships[id]
	items := make([]alliance.Membership, 0, len(members))
	for _, item := range members {
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool { return items[i].JoinedAt.Before(items[j].JoinedAt) })
	return items, nil
}

func (r *SocialRepo) SaveMembership(ctx context.Context, item alliance.Membership) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.memberships[item.AllianceID]; !ok {
		r.memberships[item.AllianceID] = make(map[player.ID]alliance.Membership)
	}
	r.memberships[item.AllianceID][item.PlayerID] = item
	return nil
}

func (r *SocialRepo) DeleteMembership(ctx context.Context, allianceID alliance.ID, playerID player.ID) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.memberships[allianceID], playerID)
	return nil
}

func (r *SocialRepo) CreateInvite(ctx context.Context, item alliance.Invite) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.invites[item.ID] = item
	return nil
}

func (r *SocialRepo) FindInvite(ctx context.Context, id alliance.InviteID) (alliance.Invite, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.invites[id]
	if !ok {
		return alliance.Invite{}, apperror.New(apperror.NotFound, "alliance invite not found")
	}
	return item, nil
}

func (r *SocialRepo) ListInvitesForPlayer(ctx context.Context, playerID player.ID) ([]alliance.Invite, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]alliance.Invite, 0)
	for _, item := range r.invites {
		if item.InviteeID == playerID && item.Status == alliance.InvitePending {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	return items, nil
}

func (r *SocialRepo) UpdateInvite(ctx context.Context, item alliance.Invite) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.invites[item.ID] = item
	return nil
}

func (r *SocialRepo) AddTreasuryEntry(ctx context.Context, item alliance.TreasuryEntry) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.treasury[item.AllianceID] = append(r.treasury[item.AllianceID], item)
	return nil
}

func (r *SocialRepo) ListTreasury(ctx context.Context, id alliance.ID, limit int) ([]alliance.TreasuryEntry, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := append([]alliance.TreasuryEntry(nil), r.treasury[id]...)
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *SocialRepo) SaveBuff(ctx context.Context, item alliance.Buff) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.buffs[item.AllianceID]; !ok {
		r.buffs[item.AllianceID] = make(map[alliance.BuffID]alliance.Buff)
	}
	r.buffs[item.AllianceID][item.ID] = item
	return nil
}

func (r *SocialRepo) ListBuffs(ctx context.Context, id alliance.ID) ([]alliance.Buff, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]alliance.Buff, 0, len(r.buffs[id]))
	for _, item := range r.buffs[id] {
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	return items, nil
}

func (r *SocialRepo) AddTerritoryAid(ctx context.Context, item alliance.TerritoryAid) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.aid[item.AllianceID] = append(r.aid[item.AllianceID], item)
	return nil
}

func (r *SocialRepo) ListTerritoryAid(ctx context.Context, id alliance.ID) ([]alliance.TerritoryAid, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	return append([]alliance.TerritoryAid(nil), r.aid[id]...), nil
}

func (r *SocialRepo) AddMessage(ctx context.Context, item chat.Message) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.messages = append(r.messages, item)
	return nil
}

func (r *SocialRepo) ListMessages(ctx context.Context, playerID player.ID, channel chat.Channel, allianceID alliance.ID, limit int) ([]chat.Message, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]chat.Message, 0)
	for _, item := range r.messages {
		if item.Channel != channel {
			continue
		}
		if channel == chat.ChannelAlliance && item.AllianceID != allianceID {
			continue
		}
		if channel == chat.ChannelPrivate && item.AuthorID != playerID && item.Recipient != playerID {
			continue
		}
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *SocialRepo) CreateOrder(ctx context.Context, item market.Order) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[item.ID] = item
	return nil
}

func (r *SocialRepo) FindOrder(ctx context.Context, id market.OrderID) (market.Order, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.orders[id]
	if !ok {
		return market.Order{}, apperror.New(apperror.NotFound, "market order not found")
	}
	return item, nil
}

func (r *SocialRepo) UpdateOrder(ctx context.Context, item market.Order) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[item.ID] = item
	return nil
}

func (r *SocialRepo) ListOrders(ctx context.Context, status market.Status, limit int) ([]market.Order, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]market.Order, 0)
	for _, item := range r.orders {
		if status == "" || item.Status == status {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}
