package player

import (
	"testing"
	"time"
)

func TestPvPProtectionBoundariesAndBudget(t *testing.T) {
	seen := time.Date(2026, 10, 30, 12, 0, 0, 0, time.UTC)
	for _, tc := range []struct {
		delay   time.Duration
		blocked bool
	}{{15*time.Minute - time.Nanosecond, false}, {15 * time.Minute, true}, {8*time.Hour + 15*time.Minute - time.Nanosecond, true}, {8*time.Hour + 15*time.Minute, false}} {
		s, n := ApplyPvPDamage(PvPState{}, seen, seen.Add(tc.delay), 80, 100)
		if (n == 0) != tc.blocked || (!s.OfflineUntil.IsZero()) != tc.blocked {
			t.Fatalf("delay %s: %+v %d", tc.delay, s, n)
		}
	}
	state := PvPState{Day: seen.UTC().Truncate(24 * time.Hour), Damage: 9990}
	state, n := ApplyPvPDamage(state, seen, seen, 80, 100)
	if n != 10 || state.Damage != 10000 {
		t.Fatal(state, n)
	}
	_, n = ApplyPvPDamage(state, seen, seen, 1, 100)
	if n != 0 {
		t.Fatal("damage budget exceeded")
	}
	state = PvPState{Day: seen.UTC().Truncate(24 * time.Hour), Destructions: 2}
	state, n = ApplyPvPDamage(state, seen, seen, 80, 80)
	if n != 80 || state.Destructions != 3 {
		t.Fatal(state, n)
	}
	_, n = ApplyPvPDamage(state, seen, seen, 1, 100)
	if n != 0 {
		t.Fatal("destruction budget exceeded")
	}
	state, n = ApplyPvPDamage(state, seen.Add(24*time.Hour), seen.Add(24*time.Hour), 80, 100)
	if n != 80 || state.Destructions != 0 || state.Damage != 80 {
		t.Fatal("UTC reset", state, n)
	}
}
