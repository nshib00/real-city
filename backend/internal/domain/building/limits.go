package building

func BuildingLimitForTownHall(buildings []Building, rules BuildRules) int {
	level := 0
	for _, b := range buildings {
		if b.Type == TypeTownHall && b.Level > level {
			level = b.Level
		}
	}
	return rules.LimitForTownHallLevel(level)
}
