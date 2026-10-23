package dto

import (
	"time"

	"real-city/backend/internal/domain/player"
)

type Profile struct {
	DisplayName  string                 `json:"display_name"`
	CityName     string                 `json:"city_name"`
	AvatarURL    string                 `json:"avatar_url"`
	Level        int                    `json:"level"`
	XP           int                    `json:"xp"`
	LevelStartXP int                    `json:"level_start_xp"`
	NextLevelXP  *int                   `json:"next_level_xp"`
	Settings     player.ProfileSettings `json:"settings"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

type UpdateProfileRequest struct {
	DisplayName string                 `json:"display_name"`
	CityName    string                 `json:"city_name"`
	AvatarURL   string                 `json:"avatar_url"`
	Settings    player.ProfileSettings `json:"settings"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password"`
	NewPassword     string `json:"new_password"`
}

type PublicPlayerResponse struct {
	ID          string `json:"id"`
	DisplayName string `json:"display_name"`
	Level       int    `json:"level"`
}

func PublicPlayer(p player.Player) PublicPlayerResponse {
	name := p.Profile.DisplayName
	if name == "" {
		name = p.Name
	}
	return PublicPlayerResponse{ID: string(p.ID), DisplayName: name, Level: p.Profile.Level}
}

func Player(p player.Player) PlayerResponse {
	return PlayerResponse{
		ID:     p.ID,
		Email:  p.Email,
		Name:   p.Name,
		Status: p.Status,
		Role:   p.Role,
		Profile: Profile{
			DisplayName:  p.Profile.DisplayName,
			CityName:     p.Profile.CityName,
			AvatarURL:    p.Profile.AvatarURL,
			Level:        p.Profile.Level,
			XP:           p.Profile.XP,
			LevelStartXP: player.LevelStartXP(p.Profile.Level),
			NextLevelXP:  nextLevelXP(p.Profile.Level),
			Settings:     p.Profile.Settings,
			UpdatedAt:    p.Profile.UpdatedAt,
		},
		CreatedAt: p.CreatedAt,
		UpdatedAt: p.UpdatedAt,
	}
}

func nextLevelXP(level int) *int {
	next := player.NextLevelXP(level)
	if next == 0 {
		return nil
	}
	return &next
}
