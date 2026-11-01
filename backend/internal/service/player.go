package service

import (
	"context"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type PlayerService struct {
	players   PlayerRepository
	sessions  SessionStore
	log       *slog.Logger
	events    *EventBus
	buildings BuildingRepository
	alliances AllianceRepository
}

type UpdateProfileInput struct {
	AvatarID     *string
	BannerID     *string
	Title        *string
	HomeCenterID *string
	DisplayName  string
	CityName     string
	AvatarURL    string
	Settings     player.ProfileSettings
}

func NewPlayerService(players PlayerRepository, sessions SessionStore, log *slog.Logger) *PlayerService {
	return &PlayerService{players: players, sessions: sessions, log: log}
}

func (s *PlayerService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *PlayerService) GetMe(ctx context.Context, id player.ID) (player.Player, error) {
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		return p, err
	}
	return s.enrichProfile(ctx, p)
}

func (s *PlayerService) GetPublic(ctx context.Context, id player.ID) (player.Player, error) {
	return s.players.FindByID(ctx, id)
}

func (s *PlayerService) UpdatePresence(ctx context.Context, id player.ID, x, y int) error {
	if x < 0 || x >= 160 || y < 0 || y >= 160 {
		return apperror.New(apperror.Validation, "invalid presence tile")
	}
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if p.Status != player.StatusActive {
		return apperror.New(apperror.Forbidden, "player is not active")
	}
	now := time.Now().UTC()
	if err := s.players.SavePresence(ctx, id, x, y, now); err != nil {
		return err
	}
	if s.events != nil {
		coord := world.Coord{X: x, Y: y}
		_ = s.events.Publish(Event{
			Type: EventPresenceMoved, ChunkID: world.ChunkID(DefaultWorldID, world.ChunkForTile(coord)),
			Payload: PresenceMovedPayload{Player: player.Presence{PlayerID: id, Name: p.Name, Level: p.Profile.Level, TileX: x, TileY: y, UpdatedAt: now}},
		})
	}
	return nil
}

func (s *PlayerService) NearbyPresence(ctx context.Context, viewer player.ID, x, y, radius int) ([]player.Presence, error) {
	if x < 0 || x >= 160 || y < 0 || y >= 160 || radius < 1 || radius > 80 {
		return nil, apperror.New(apperror.Validation, "invalid presence viewport")
	}
	return s.players.ListNearbyPresence(ctx, viewer, x, y, radius, time.Now().UTC().Add(-20*time.Second))
}

func (s *PlayerService) UpdateProfile(ctx context.Context, id player.ID, input UpdateProfileInput) (player.Player, error) {
	current, err := s.players.FindByID(ctx, id)
	if err != nil {
		return player.Player{}, err
	}
	profile := current.Profile
	profile.DisplayName = input.DisplayName
	profile.CityName = input.CityName
	profile.AvatarURL = input.AvatarURL
	profile.Settings = input.Settings
	profile.UpdatedAt = time.Now().UTC()
	if input.AvatarID != nil {
		profile.AvatarID = *input.AvatarID
	}
	if input.BannerID != nil {
		profile.BannerID = *input.BannerID
	}
	if input.Title != nil {
		profile.Title = *input.Title
	}
	if input.HomeCenterID != nil {
		profile.HomeCenterID = *input.HomeCenterID
		if profile.HomeCenterID != "" {
			if s.buildings == nil {
				return player.Player{}, apperror.New(apperror.Conflict, "Поселения временно недоступны")
			}
			b, e := s.buildings.FindByID(ctx, building.ID(profile.HomeCenterID))
			if e != nil {
				return player.Player{}, e
			}
			if b.OwnerID != string(id) || b.Type != building.TypeTownHall || b.State == building.StateRuined {
				return player.Player{}, apperror.New(apperror.Forbidden, "Выберите свою действующую ратушу")
			}
		}
	}
	if err := player.ValidateAppearance(profile); err != nil {
		return player.Player{}, err
	}

	profile = player.NormalizeProfile(profile)
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

func (s *PlayerService) AwardXP(ctx context.Context, id player.ID, amount int, reason string) (player.Player, error) {
	if amount <= 0 {
		return player.Player{}, apperror.WithFields(apperror.Validation, "invalid experience reward", map[string]string{
			"amount": "must be greater than zero",
		})
	}
	current, err := s.players.FindByID(ctx, id)
	if err != nil {
		return player.Player{}, err
	}
	nextXP := current.Profile.XP + amount
	nextLevel := player.LevelForXP(nextXP)
	updated, err := s.players.UpdateProgress(ctx, id, nextXP, nextLevel)
	if err != nil {
		return player.Player{}, err
	}
	s.log.Info("player.xp_awarded", "event", "player.xp_awarded", "player_id", id, "amount", amount, "reason", reason, "level", nextLevel)
	if nextLevel > current.Profile.Level {
		s.log.Info("player.level_changed", "event", "player.level_changed", "player_id", id, "from", current.Profile.Level, "to", nextLevel)
	}
	return updated, nil
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
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if p.Role == player.RoleAdmin {
		return apperror.New(apperror.Conflict, "Перед удалением передайте роль администратора и снимите её с этого аккаунта")
	}
	if err := s.sessions.RevokePlayer(ctx, id); err != nil {
		return err
	}
	if err := s.players.Delete(ctx, id); err != nil {
		return err
	}
	s.log.Info("player.deleted", "event", "player.deleted", "player_id", id)
	return nil
}
