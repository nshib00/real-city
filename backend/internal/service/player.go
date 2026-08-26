package service

import (
	"context"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/player"
)

type PlayerService struct {
	players  PlayerRepository
	sessions SessionStore
	log      *slog.Logger
}

type UpdateProfileInput struct {
	DisplayName string
	AvatarURL   string
	Settings    player.ProfileSettings
}

func NewPlayerService(players PlayerRepository, sessions SessionStore, log *slog.Logger) *PlayerService {
	return &PlayerService{players: players, sessions: sessions, log: log}
}

func (s *PlayerService) GetMe(ctx context.Context, id player.ID) (player.Player, error) {
	return s.players.FindByID(ctx, id)
}

func (s *PlayerService) UpdateProfile(ctx context.Context, id player.ID, input UpdateProfileInput) (player.Player, error) {
	profile := player.Profile{
		DisplayName: input.DisplayName,
		AvatarURL:   input.AvatarURL,
		Settings:    input.Settings,
		UpdatedAt:   time.Now().UTC(),
	}
	if profile.Settings.RenderQuality == "" {
		profile.Settings.RenderQuality = player.RenderQualityMedium
	}
	if err := player.ValidateProfile(profile); err != nil {
		return player.Player{}, err
	}
	p, err := s.players.UpdateProfile(ctx, id, profile)
	if err != nil {
		return player.Player{}, err
	}
	s.log.Info("player.profile_updated", "event", "player.profile_updated", "player_id", id)
	return p, nil
}

func (s *PlayerService) ChangePassword(ctx context.Context, id player.ID, currentPassword string, newPassword string) error {
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if err := player.ComparePassword(p.PasswordHash, currentPassword); err != nil {
		return err
	}
	hash, err := player.HashPassword(newPassword)
	if err != nil {
		return err
	}
	if err := s.players.UpdatePasswordHash(ctx, id, hash); err != nil {
		return err
	}
	if err := s.sessions.RevokePlayer(ctx, id); err != nil {
		return err
	}
	s.log.Info("player.password_changed", "event", "player.password_changed", "player_id", id)
	return nil
}

func (s *PlayerService) DeleteMe(ctx context.Context, id player.ID) error {
	if err := s.sessions.RevokePlayer(ctx, id); err != nil {
		return err
	}
	if err := s.players.Delete(ctx, id); err != nil {
		return err
	}
	s.log.Info("player.deleted", "event", "player.deleted", "player_id", id)
	return nil
}
