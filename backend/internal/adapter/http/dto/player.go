package dto

import (
	"time"

	"real-city/backend/internal/domain/player"
)

type Profile struct {
	DisplayName string                 `json:"display_name"`
	AvatarURL   string                 `json:"avatar_url"`
	Settings    player.ProfileSettings `json:"settings"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type UpdateProfileRequest struct {
	DisplayName string                 `json:"display_name"`
	AvatarURL   string                 `json:"avatar_url"`
	Settings    player.ProfileSettings `json:"settings"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password"`
	NewPassword     string `json:"new_password"`
}

func Player(p player.Player) PlayerResponse {
	return PlayerResponse{
		ID:        p.ID,
		Email:     p.Email,
		Name:      p.Name,
		Status:    p.Status,
		Role:      p.Role,
		Profile:   Profile{DisplayName: p.Profile.DisplayName, AvatarURL: p.Profile.AvatarURL, Settings: p.Profile.Settings, UpdatedAt: p.Profile.UpdatedAt},
		CreatedAt: p.CreatedAt,
		UpdatedAt: p.UpdatedAt,
	}
}
