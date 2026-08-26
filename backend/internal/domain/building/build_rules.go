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
	return r.BaseLimit + (level-1)*5
}

func InitialState(duration time.Duration) State {
	if duration <= 0 {
		return StateActive
	}
	return StateBuilding
}
