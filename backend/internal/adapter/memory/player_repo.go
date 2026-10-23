package memory

import (
	"context"
	"sync"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type PlayerRepo struct {
	mu       sync.RWMutex
	players  map[player.ID]player.Player
	emailID  map[string]player.ID
	nameID   map[string]player.ID
	xpEvents map[string]bool
	presence map[player.ID]player.Presence
}

func NewPlayerRepo() *PlayerRepo {
	return &PlayerRepo{
		players:  make(map[player.ID]player.Player),
		emailID:  make(map[string]player.ID),
		nameID:   make(map[string]player.ID),
		xpEvents: make(map[string]bool),
		presence: make(map[player.ID]player.Presence),
	}
}

func (r *PlayerRepo) Create(ctx context.Context, p player.Player) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	email := player.NormalizeEmail(p.Email)
	if _, ok := r.emailID[email]; ok {
		return apperror.New(apperror.Conflict, "email is already taken")
	}
	if _, ok := r.nameID[p.Name]; ok {
		return apperror.New(apperror.Conflict, "name is already taken")
	}
	p.Email = email
	if p.Role == "" {
		p.Role = player.RoleUser
	}
	r.players[p.ID] = p
	r.emailID[email] = p.ID
	r.nameID[p.Name] = p.ID
	return nil
}

func (r *PlayerRepo) FindByID(ctx context.Context, id player.ID) (player.Player, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	p, ok := r.players[id]
	if !ok || p.Status == player.StatusDeleted {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	return p, nil
}

func (r *PlayerRepo) FindByEmail(ctx context.Context, email string) (player.Player, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	id, ok := r.emailID[player.NormalizeEmail(email)]
	if !ok {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	p := r.players[id]
	if p.Status == player.StatusDeleted {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	return p, nil
}

func (r *PlayerRepo) UpdateProfile(ctx context.Context, id player.ID, profile player.Profile) (player.Player, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok || p.Status == player.StatusDeleted {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	profile.Level = p.Profile.Level
	profile.XP = p.Profile.XP
	profile.UpdatedAt = time.Now().UTC()
	p.Profile = profile
	p.UpdatedAt = profile.UpdatedAt
	r.players[id] = p
	return p, nil
}

func (r *PlayerRepo) UpdateProgress(ctx context.Context, id player.ID, xp int, level int) (player.Player, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok || p.Status == player.StatusDeleted {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	p.Profile.XP = xp
	p.Profile.Level = level
	p.Profile.UpdatedAt = time.Now().UTC()
	p.UpdatedAt = p.Profile.UpdatedAt
	r.players[id] = p
	return p, nil
}

func (r *PlayerRepo) AwardXPEvent(ctx context.Context, id player.ID, amount int, reason string, eventKey string) (bool, error) {
	_ = ctx
	_ = reason
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok || p.Status == player.StatusDeleted {
		return false, apperror.New(apperror.NotFound, "player not found")
	}
	if r.xpEvents[eventKey] {
		return false, nil
	}
	p.Profile.XP += amount
	p.Profile.Level = player.LevelForXP(p.Profile.XP)
	p.Profile.UpdatedAt = time.Now().UTC()
	p.UpdatedAt = p.Profile.UpdatedAt
	r.players[id] = p
	r.xpEvents[eventKey] = true
	return true, nil
}

func (r *PlayerRepo) UpdatePasswordHash(ctx context.Context, id player.ID, passwordHash string) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok || p.Status == player.StatusDeleted {
		return apperror.New(apperror.NotFound, "player not found")
	}
	p.PasswordHash = passwordHash
	p.UpdatedAt = time.Now().UTC()
	r.players[id] = p
	return nil
}

func (r *PlayerRepo) Delete(ctx context.Context, id player.ID) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok {
		return apperror.New(apperror.NotFound, "player not found")
	}
	p.Status = player.StatusDeleted
	p.UpdatedAt = time.Now().UTC()
	r.players[id] = p
	delete(r.presence, id)
	return nil
}

func (r *PlayerRepo) SavePresence(ctx context.Context, id player.ID, x, y int, now time.Time) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok || p.Status != player.StatusActive {
		return apperror.New(apperror.NotFound, "player not found")
	}
	r.presence[id] = player.Presence{PlayerID: id, TileX: x, TileY: y, UpdatedAt: now}
	return nil
}

func (r *PlayerRepo) ListNearbyPresence(ctx context.Context, viewer player.ID, x, y, radius int, since time.Time) ([]player.Presence, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]player.Presence, 0)
	for id, presence := range r.presence {
		p := r.players[id]
		if id == viewer || p.Status != player.StatusActive || presence.UpdatedAt.Before(since) || wrappedTileDistance(x, presence.TileX) > radius || wrappedTileDistance(y, presence.TileY) > radius {
			continue
		}
		presence.Name = p.Name
		presence.Level = p.Profile.Level
		items = append(items, presence)
	}
	return items, nil
}

func wrappedTileDistance(first, second int) int {
	distance := first - second
	if distance < 0 {
		distance = -distance
	}
	if distance > 80 {
		return 160 - distance
	}
	return distance
}
