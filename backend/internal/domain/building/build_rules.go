package building

import "time"

type BuildRules struct {
	BaseLimit int
}

func (r BuildRules) LimitForTownHallLevel(level int) int {
	if r.BaseLimit <= 0 {
		r.BaseLimit = 8
	}
	if level <= 0 {
		return r.BaseLimit
	}
	return r.BaseLimit + (level-1)*3
}

func InitialState(duration time.Duration) State {
	if duration <= 0 {
		return StateActive
	}
	return StateBuilding
}

const RushCompletionStep = 3 * time.Minute

func RushCompletionCrystalCost(remaining time.Duration) int {
	if remaining <= 0 {
		return 0
	}
	if remaining < RushCompletionStep {
		return 1
	}
	// Explicit balance rule: under 3 minutes costs 1 crystal; from 3:00 onward
	// each started 3-minute block costs one more crystal.
	return 2 + int((remaining-RushCompletionStep)/RushCompletionStep)
}
