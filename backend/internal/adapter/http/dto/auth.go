package dto

import (
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type RegisterRequest struct {
	Email    string `json:"email"`
	Name     string `json:"name"`
	Password string `json:"password"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type RefreshRequest struct {
	RefreshToken string `json:"refresh_token"`
}

type LogoutRequest struct {
	RefreshToken string `json:"refresh_token"`
	AllDevices   bool   `json:"all_devices"`
}

type AuthResponse struct {
	Player       PlayerResponse `json:"player"`
	AccessToken  string         `json:"access_token"`
	RefreshToken string         `json:"refresh_token"`
	AccessUntil  time.Time      `json:"access_until"`
	RefreshUntil time.Time      `json:"refresh_until"`
}

func (r RegisterRequest) Validate() error {
	fields := map[string]string{}
	if r.Email == "" {
		fields["email"] = "is required"
	}
	if r.Name == "" {
		fields["name"] = "is required"
	}
	if r.Password == "" {
		fields["password"] = "is required"
	}
	if len(fields) > 0 {
		return apperror.WithFields(apperror.Validation, "invalid register request", fields)
	}
	return nil
}

func (r LoginRequest) Validate() error {
	fields := map[string]string{}
	if r.Email == "" {
		fields["email"] = "is required"
	}
	if r.Password == "" {
		fields["password"] = "is required"
	}
	if len(fields) > 0 {
		return apperror.WithFields(apperror.Validation, "invalid login request", fields)
	}
	return nil
}

func AuthResult(result service.AuthResult) AuthResponse {
	return AuthResponse{
		Player:       Player(result.Player),
		AccessToken:  result.AccessToken,
		RefreshToken: result.RefreshToken,
		AccessUntil:  result.AccessUntil,
		RefreshUntil: result.RefreshUntil,
	}
}

type PlayerResponse struct {
	ID        player.ID     `json:"id"`
	Email     string        `json:"email"`
	Name      string        `json:"name"`
	Status    player.Status `json:"status"`
	Role      player.Role   `json:"role"`
	Profile   Profile       `json:"profile"`
	CreatedAt time.Time     `json:"created_at"`
	UpdatedAt time.Time     `json:"updated_at"`
}
