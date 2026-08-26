package memory

import (
	"context"
	"sync"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type PlayerRepo struct {
	mu      sync.RWMutex
	players map[player.ID]player.Player
	emailID map[string]player.ID
	nameID  map[string]player.ID
}

func NewPlayerRepo() *PlayerRepo {
	return &PlayerRepo{
		players: make(map[player.ID]player.Player),
		emailID: make(map[string]player.ID),
		nameID:  make(map[string]player.ID),
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
	profile.UpdatedAt = time.Now().UTC()
	p.Profile = profile
	p.UpdatedAt = profile.UpdatedAt
	r.players[id] = p
	return p, nil
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
	return nil
}
