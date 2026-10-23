package service

import (
	"context"
	"log/slog"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ExperienceService struct {
	players PlayerRepository
	log     *slog.Logger
}

func NewExperienceService(players PlayerRepository, log *slog.Logger) *ExperienceService {
	return &ExperienceService{players: players, log: log}
}

func (s *ExperienceService) Award(ctx context.Context, id player.ID, amount int, reason string, eventKey string) error {
	if amount <= 0 {
		return nil
	}
	if eventKey == "" {
		return apperror.New(apperror.Validation, "experience event key is required")
	}
	applied, err := s.players.AwardXPEvent(ctx, id, amount, reason, eventKey)
	if err != nil {
		return err
	}
	if applied {
		s.log.Info("player.xp_awarded", "player_id", id, "amount", amount, "reason", reason, "event_key", eventKey)
	}
	return nil
}
