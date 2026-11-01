package memory

import (
	"context"
	"maps"
	"slices"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
)

type SocialRepo struct {
	mu              sync.RWMutex
	alliances       map[alliance.ID]alliance.Alliance
	memberships     map[alliance.ID]map[player.ID]alliance.Membership
	invites         map[alliance.InviteID]alliance.Invite
	treasury        map[alliance.ID][]alliance.TreasuryEntry
	buffs           map[alliance.ID]map[alliance.BuffID]alliance.Buff
	aid             map[alliance.ID][]alliance.TerritoryAid
	messages        []chat.Message
	orders          map[market.OrderID]market.Order
	reads           map[string]time.Time
	moderationAudit []chat.ModerationAudit
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
		reads:       make(map[string]time.Time),
	}
}

func (r *SocialRepo) Create(ctx context.Context, item alliance.Alliance) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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

func (r *SocialRepo) UpdateLeader(ctx context.Context, id alliance.ID, p player.ID) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.Lock()
	defer r.mu.Unlock()
	a := r.alliances[id]
	a.LeaderID = p
	r.alliances[id] = a
	return nil
}

func (r *SocialRepo) ReadAt(ctx context.Context, p player.ID, scope string) (time.Time, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.reads[string(p)+":"+scope], nil
}
func (r *SocialRepo) SaveReadAt(ctx context.Context, p player.ID, scope string, at time.Time) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.Lock()
	defer r.mu.Unlock()
	key := string(p) + ":" + scope
	if r.reads == nil {
		r.reads = map[string]time.Time{}
	}
	if at.After(r.reads[key]) {
		r.reads[key] = at
	}
	return nil
}
func (r *SocialRepo) CountUnread(ctx context.Context, p player.ID, ch chat.Channel, id alliance.ID, after time.Time) (int, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.RLock()
	defer r.mu.RUnlock()
	n := 0
	for _, m := range r.messages {
		if m.Channel != ch || m.AuthorID == p || m.Flagged || !m.CreatedAt.After(after) {
			continue
		}
		if ch == chat.ChannelAlliance && m.AllianceID != id {
			continue
		}
		if ch == chat.ChannelPrivate && m.Recipient != p {
			continue
		}
		if ch == chat.ChannelNearby && !slices.Contains(m.Audience, p) {
			continue
		}
		n++
	}
	return n, nil
}

func (r *SocialRepo) DeleteAlliance(ctx context.Context, id alliance.ID) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.alliances, id)
	delete(r.memberships, id)
	delete(r.treasury, id)
	delete(r.buffs, id)
	delete(r.aid, id)
	messages := r.messages[:0]
	for _, message := range r.messages {
		if message.AllianceID != id {
			messages = append(messages, message)
		}
	}
	r.messages = messages
	for key, v := range r.invites {
		if v.AllianceID == id {
			delete(r.invites, key)
		}
	}
	return nil
}
func (r *SocialRepo) LockAlliance(ctx context.Context, id alliance.ID) error { return nil }
func (r *SocialRepo) Snapshot() func() {
	r.mu.RLock()
	alliances := maps.Clone(r.alliances)
	members := maps.Clone(r.memberships)
	for id, v := range members {
		members[id] = maps.Clone(v)
	}
	invites := maps.Clone(r.invites)
	orders := maps.Clone(r.orders)
	treasury := maps.Clone(r.treasury)
	buffs := maps.Clone(r.buffs)
	aid := maps.Clone(r.aid)
	for id, v := range treasury {
		treasury[id] = append([]alliance.TreasuryEntry(nil), v...)
	}
	for id, v := range buffs {
		buffs[id] = maps.Clone(v)
	}
	for id, v := range aid {
		aid[id] = append([]alliance.TerritoryAid(nil), v...)
	}
	messages := append([]chat.Message(nil), r.messages...)
	audit := append([]chat.ModerationAudit(nil), r.moderationAudit...)
	r.mu.RUnlock()
	return func() {
		r.mu.Lock()
		defer r.mu.Unlock()
		r.alliances = alliances
		r.memberships = members
		r.invites = invites
		r.orders = orders
		r.treasury = treasury
		r.buffs = buffs
		r.aid = aid
		r.messages = messages
		r.moderationAudit = audit
	}
}

func (r *SocialRepo) SaveMembership(ctx context.Context, item alliance.Membership) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.memberships[allianceID], playerID)
	return nil
}

func (r *SocialRepo) CreateInvite(ctx context.Context, item alliance.Invite) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.invites[item.ID] = item
	return nil
}

func (r *SocialRepo) FindInvite(ctx context.Context, id alliance.InviteID) (alliance.Invite, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.invites[item.ID] = item
	return nil
}

func (r *SocialRepo) AddTreasuryEntry(ctx context.Context, item alliance.TreasuryEntry) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.treasury[item.AllianceID] = append(r.treasury[item.AllianceID], item)
	return nil
}

func (r *SocialRepo) ListTreasury(ctx context.Context, id alliance.ID, limit int) ([]alliance.TreasuryEntry, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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

func (r *SocialRepo) LockMarket(ctx context.Context, resource economy.ResourceType) error { return nil }
func (r *SocialRepo) FindMatch(ctx context.Context, item market.Order) (market.Order, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	candidates := []market.Order{}
	for _, o := range r.orders {
		if o.Status != market.StatusOpen || o.PlayerID == item.PlayerID || o.Side == item.Side || o.Resource != item.Resource || market.TradeQuantity(o, item) == 0 {
			continue
		}
		left, right := int64(o.Price)*int64(item.Amount), int64(item.Price)*int64(o.Amount)
		if item.Side == market.SideBuy && left > right || item.Side == market.SideSell && left < right {
			continue
		}
		candidates = append(candidates, o)
	}
	sort.Slice(candidates, func(i, j int) bool {
		a, b := candidates[i], candidates[j]
		left, right := int64(a.Price)*int64(b.Amount), int64(b.Price)*int64(a.Amount)
		if left != right {
			if item.Side == market.SideBuy {
				return left < right
			}
			return left > right
		}
		if !a.CreatedAt.Equal(b.CreatedAt) {
			return a.CreatedAt.Before(b.CreatedAt)
		}
		return a.ID < b.ID
	})
	if len(candidates) == 0 {
		return market.Order{}, apperror.New(apperror.NotFound, "matching order not found")
	}
	return candidates[0], nil
}
func (r *SocialRepo) TreasuryBalance(ctx context.Context, id alliance.ID) (map[economy.ResourceType]int, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	balance := map[economy.ResourceType]int{}
	for _, v := range r.treasury[id] {
		if v.Kind == alliance.LedgerDonation {
			balance[v.Resource] += v.Amount
		} else {
			balance[v.Resource] -= v.Amount
		}
	}
	return balance, nil
}

func (r *SocialRepo) SaveBuff(ctx context.Context, item alliance.Buff) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.aid[item.AllianceID] = append(r.aid[item.AllianceID], item)
	return nil
}

func (r *SocialRepo) ListTerritoryAid(ctx context.Context, id alliance.ID) ([]alliance.TerritoryAid, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	return append([]alliance.TerritoryAid(nil), r.aid[id]...), nil
}

func (r *SocialRepo) AddMessage(ctx context.Context, item chat.Message) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.messages = append(r.messages, item)
	return nil
}

func (r *SocialRepo) ListMessages(ctx context.Context, playerID player.ID, channel chat.Channel, allianceID alliance.ID, limit int, before ...chat.Cursor) ([]chat.Message, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
		if channel == chat.ChannelNearby && !slices.Contains(item.Audience, playerID) {
			continue
		}
		if len(before) > 0 && !before[0].CreatedAt.IsZero() && (item.CreatedAt.After(before[0].CreatedAt) || item.CreatedAt.Equal(before[0].CreatedAt) && item.ID >= before[0].ID) {
			continue
		}
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].CreatedAt.Equal(items[j].CreatedAt) {
			return items[i].ID > items[j].ID
		}
		return items[i].CreatedAt.After(items[j].CreatedAt)
	})
	if limit <= 0 || limit > 100 {
		limit = 100
	}
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *SocialRepo) CreateOrder(ctx context.Context, item market.Order) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[item.ID] = item
	return nil
}

func (r *SocialRepo) FindOrder(ctx context.Context, id market.OrderID) (market.Order, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[item.ID] = item
	return nil
}

func (r *SocialRepo) ListOrders(ctx context.Context, status market.Status, limit int) ([]market.Order, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
