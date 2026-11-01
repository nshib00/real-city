package player

import "time"

type XPAudit struct {
	PlayerID  ID
	Reason    string
	Requested int
	Amount    int
	At        time.Time
}

// Caps group related actions across all targets; changing nodes or rebuilding a target
// does not reset diminishing returns. Daily boundaries are UTC.
func CappedXP(requested int, reason string, count, earned, allEarned int) int {
	if requested <= 0 {
		return 0
	}
	cap, full, divisor := 250000, 20, 2
	switch reason {
	case "forest:chop", "resource:harvest":
		cap, full, divisor = 100, 50, 2
		if count >= 100 {
			return 0
		}
	case "resource:claim":
		cap, full, divisor = 1000, 20, 2
	case "field:harvest", "production:complete":
	case "monster:kill":
		cap, full, divisor = 100000, 50, 2
	case "building:complete":
		cap, full, divisor = 1000000, 50, 2
	case "building:destroy":
		cap, full, divisor = 500000, 10, 10
	default:
		return requested
	}
	grant := requested
	if count >= full {
		grant = max(1, grant/divisor)
	}
	if count >= 5*full {
		grant = max(1, grant/divisor)
	}
	return max(0, min(grant, cap-earned, 2000000-allEarned))
}
