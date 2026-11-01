package player

import (
	"real-city/backend/pkg/apperror"
	"regexp"
	"strings"
	"unicode/utf8"
)

var appearanceID = regexp.MustCompile(`^[a-z0-9_-]{1,48}$`)

func ValidateAppearance(p Profile) error {
	for _, id := range []string{p.AvatarID, p.BannerID} {
		if id != "" && !appearanceID.MatchString(id) {
			return apperror.New(apperror.Validation, "Идентификатор оформления должен содержать латинские буквы, цифры, _ или -")
		}
	}
	if utf8.RuneCountInString(strings.TrimSpace(p.Title)) > 80 {
		return apperror.New(apperror.Validation, "Титул должен быть не длиннее 80 символов")
	}
	return nil
}

type SettlementRegion struct {
	DistrictX int `json:"district_x"`
	DistrictY int `json:"district_y"`
}

// Deliberately excludes email, exact XP, settings, resource balances and home object id.
type PublicProfile struct {
	PlayerID         ID                `json:"player_id"`
	DisplayName      string            `json:"display_name"`
	AvatarID         string            `json:"avatar_id"`
	BannerID         string            `json:"banner_id"`
	Title            string            `json:"title"`
	Level            int               `json:"level"`
	GroupID          string            `json:"group_id,omitempty"`
	Scores           map[string]int    `json:"scores"`
	SettlementRegion *SettlementRegion `json:"settlement_region,omitempty"`
}
