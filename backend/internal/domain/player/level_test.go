package player

import "testing"

func TestLevelStartXPMatchesCumulativeThreshold(t *testing.T) {
	for _, test := range []struct {
		xp, level, start, next int
	}{
		{0, 1, 0, 200},
		{199, 1, 0, 200},
		{200, 2, 200, 700},
		{699, 2, 200, 700},
		{700, 3, 700, 1900},
		{1899, 3, 700, 1900},
		{1900, 4, 1900, 4700},
		{4700, 5, 4700, 11200},
		{11200, 6, 11200, 26200},
		{26200, 7, 26200, 61200},
		{61200, 8, 61200, 141200},
		{141200, 9, 141200, 321200},
		{321200, 10, 321200, 721200},
		{721200, 11, 721200, 1621200},
		{1621200, 12, 1621200, 3621200},
		{3621200, 13, 3621200, 8121200},
		{8121200, 14, 8121200, 18121200},
		{18121200, 15, 18121200, 0},
		{18121201, 15, 18121200, 0},
	} {
		level := LevelForXP(test.xp)
		if level != test.level || LevelStartXP(level) != test.start || NextLevelXP(level) != test.next {
			t.Fatalf("unexpected level progress at %d XP: level %d, start %d, next %d", test.xp, level, LevelStartXP(level), NextLevelXP(level))
		}
	}
}
