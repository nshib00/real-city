package service

import (
	"sync"

	"real-city/backend/internal/domain/player"
)

type PresenceService struct {
	mu      sync.RWMutex
	players map[player.ID]bool
}

func NewPresenceService() *PresenceService {
	return &PresenceService{players: make(map[player.ID]bool)}
}

func (s *PresenceService) SetOnline(id player.ID, online bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if online {
		s.players[id] = true
		return
	}
	delete(s.players, id)
}

func (s *PresenceService) IsOnline(id player.ID) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.players[id]
}
