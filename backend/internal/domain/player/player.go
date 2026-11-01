package player

import (
	"strings"
	"time"
	"unicode/utf8"

	"real-city/backend/pkg/apperror"
)

type ID string
type SessionID string

type Status string
type Role string

const (
	StatusActive    Status = "active"
	StatusSuspended Status = "suspended"
	StatusDeleted   Status = "deleted"
)

const (
	RoleUser  Role = "user"
	RoleAdmin Role = "admin"
)

type NotificationSettings struct {
	AttackAlerts    bool `json:"attack_alerts"`
	ProductionReady bool `json:"production_ready"`
	MarketUpdates   bool `json:"market_updates"`
}

type RenderQuality string

const (
	RenderQualityLow    RenderQuality = "low"
	RenderQualityMedium RenderQuality = "medium"
	RenderQualityHigh   RenderQuality = "high"
)

type ProfileSettings struct {
	Notifications NotificationSettings `json:"notifications"`
	RenderQuality RenderQuality        `json:"render_quality"`
}

type Profile struct {
	AvatarID     string          `json:"avatar_id"`
	BannerID     string          `json:"banner_id"`
	Title        string          `json:"title"`
	GroupID      string          `json:"group_id,omitempty"`
	HomeCenterID string          `json:"home_center_id,omitempty"`
	Scores       map[string]int  `json:"scores,omitempty"`
	DisplayName  string          `json:"display_name"`
	CityName     string          `json:"city_name"`
	AvatarURL    string          `json:"avatar_url"`
	Level        int             `json:"level"`
	XP           int             `json:"xp"`
	Settings     ProfileSettings `json:"settings"`
	UpdatedAt    time.Time       `json:"updated_at"`
}

type Player struct {
	ID           ID        `json:"id"`
	Email        string    `json:"email"`
	Name         string    `json:"name"`
	PasswordHash string    `json:"-"`
	Status       Status    `json:"status"`
	Role         Role      `json:"role"`
	Profile      Profile   `json:"profile"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type Session struct {
	ID               SessionID `json:"id"`
	PlayerID         ID        `json:"player_id"`
	RefreshTokenHash string    `json:"-"`
	UserAgent        string    `json:"user_agent"`
	IP               string    `json:"ip"`
	ExpiresAt        time.Time `json:"expires_at"`
	RevokedAt        time.Time `json:"revoked_at,omitempty"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

func DefaultProfile(name string, now time.Time) Profile {
	return Profile{
		DisplayName: name,
		CityName:    name,
		Level:       1,
		XP:          0,
		Settings: ProfileSettings{
			Notifications: NotificationSettings{
				AttackAlerts:    true,
				ProductionReady: true,
				MarketUpdates:   false,
			},
			RenderQuality: RenderQualityMedium,
		},
		UpdatedAt: now,
	}
}

func NormalizeEmail(email string) string {
	return strings.ToLower(strings.TrimSpace(email))
}

func ValidateEmail(email string) error {
	email = NormalizeEmail(email)
	if len(email) < 5 || len(email) > 254 || !strings.Contains(email, "@") {
		return apperror.WithFields(apperror.Validation, "invalid player data", map[string]string{
			"email": "must be a valid email address",
		})
	}
	return nil
}

func ValidateName(name string) error {
	name = strings.TrimSpace(name)
	if len(name) < 3 || len(name) > 32 {
		return apperror.WithFields(apperror.Validation, "invalid player data", map[string]string{
			"name": "must be between 3 and 32 characters",
		})
	}
	for _, char := range name {
		if char == '_' || char == '-' || char == ' ' {
			continue
		}
		if char >= 'a' && char <= 'z' || char >= 'A' && char <= 'Z' || char >= '0' && char <= '9' {
			continue
		}
		return apperror.WithFields(apperror.Validation, "invalid player data", map[string]string{
			"name": "may contain letters, numbers, spaces, underscores and hyphens",
		})
	}
	return nil
}

func LevelForXP(xp int) int {
	if xp <= 0 {
		return 1
	}
	level := 1
	for index, threshold := range levelThresholds {
		if xp >= threshold {
			level = index + 1
		}
	}
	return level
}

func NextLevelXP(level int) int {
	if level < 1 {
		level = 1
	}
	if level >= len(levelThresholds) {
		return 0
	}
	return levelThresholds[level]
}

func LevelStartXP(level int) int {
	if level < 1 {
		return levelThresholds[0]
	}
	if level >= len(levelThresholds) {
		return levelThresholds[len(levelThresholds)-1]
	}
	return levelThresholds[level-1]
}

func NormalizeProfile(profile Profile) Profile {
	profile.Title = strings.TrimSpace(profile.Title)
	profile.DisplayName = strings.TrimSpace(profile.DisplayName)
	profile.CityName = strings.TrimSpace(profile.CityName)
	profile.AvatarURL = strings.TrimSpace(profile.AvatarURL)
	if profile.CityName == "" {
		profile.CityName = profile.DisplayName
	}
	if profile.XP < 0 {
		profile.XP = 0
	}
	profile.Level = LevelForXP(profile.XP)
	if profile.Settings.RenderQuality == "" {
		profile.Settings.RenderQuality = RenderQualityMedium
	}
	return profile
}

func ValidateProfile(profile Profile) error {
	profile = NormalizeProfile(profile)
	if err := ValidateName(profile.DisplayName); err != nil {
		return err
	}
	if err := validateCityName(profile.CityName); err != nil {
		return err
	}
	switch profile.Settings.RenderQuality {
	case "", RenderQualityLow, RenderQualityMedium, RenderQualityHigh:
		return nil
	default:
		return apperror.WithFields(apperror.Validation, "invalid profile settings", map[string]string{
			"render_quality": "must be low, medium or high",
		})
	}
}

func validateCityName(name string) error {
	name = strings.TrimSpace(name)
	length := utf8.RuneCountInString(name)
	if length < 3 || length > 40 {
		return apperror.WithFields(apperror.Validation, "invalid player data", map[string]string{
			"city_name": "must be between 3 and 40 characters",
		})
	}
	return nil
}
