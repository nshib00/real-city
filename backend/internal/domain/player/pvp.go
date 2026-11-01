package player

import "time"

const PvPDailyDamage = 10000
const PvPDailyDestructions = 3

type PvPState struct {
	Day          time.Time `json:"day"`
	Damage       int       `json:"damage"`
	Destructions int       `json:"destructions"`
	OfflineUntil time.Time `json:"offline_until"`
}

// Grace prevents disconnecting from cancelling an ongoing attack. Protection
// expires after eight hours; reconnecting does not reset the daily loss budget.
func ApplyPvPDamage(state PvPState, lastSeen, now time.Time, damage, health int) (PvPState, int) {
	day := now.UTC().Truncate(24 * time.Hour)
	if !state.Day.Equal(day) {
		state = PvPState{Day: day}
	}
	start := lastSeen.Add(15 * time.Minute)
	state.OfflineUntil = time.Time{}
	if !lastSeen.IsZero() && !now.Before(start) && now.Before(start.Add(8*time.Hour)) {
		state.OfflineUntil = start.Add(8 * time.Hour)
	}
	if !state.OfflineUntil.IsZero() || state.Destructions >= PvPDailyDestructions || state.Damage >= PvPDailyDamage {
		return state, 0
	}
	if damage <= 0 || health <= 0 {
		return state, 0
	}
	allowed := min(damage, health, PvPDailyDamage-state.Damage)
	state.Damage += allowed
	if allowed == health {
		state.Destructions++
	}
	return state, allowed
}
