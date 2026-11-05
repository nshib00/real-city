package dto

import (
	"encoding/json"
	"testing"

	"real-city/backend/internal/domain/player"
)

func TestPlayerLevelProgressMatchesSpecification(t *testing.T) {
	for _, test := range []struct {
		xp, level, start, next int
	}{
		{199, 1, 0, 200},
		{700, 3, 700, 1900},
		{18121200, 15, 18121200, 0},
	} {
		item := player.Player{Profile: player.Profile{XP: test.xp, Level: player.LevelForXP(test.xp)}}
		profile := Player(item).Profile
		if profile.Level != test.level || profile.LevelStartXP != test.start {
			t.Fatalf("unexpected progress at %d XP: %#v", test.xp, profile)
		}
		if test.next == 0 && profile.NextLevelXP != nil {
			t.Fatalf("max level should have no next level XP, got %d", *profile.NextLevelXP)
		}
		if test.next > 0 && (profile.NextLevelXP == nil || *profile.NextLevelXP != test.next) {
			t.Fatalf("unexpected next level XP at %d: %#v", test.xp, profile.NextLevelXP)
		}
	}
}

func TestPlayerProfileOmitsRemovedScores(t *testing.T) {
	response := Player(player.Player{Profile: player.Profile{XP: 100}})
	raw, err := json.Marshal(response.Profile)
	if err != nil {
		t.Fatal(err)
	}
	var fields map[string]any
	if err := json.Unmarshal(raw, &fields); err != nil {
		t.Fatal(err)
	}
	if _, exists := fields["scores"]; exists {
		t.Fatal("profile must not expose removed scores")
	}
	if _, exists := fields["xp"]; !exists {
		t.Fatal("profile must retain XP")
	}
}
