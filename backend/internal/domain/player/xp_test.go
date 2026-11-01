package player

import "testing"

func TestXPDiminishingAndCaps(t *testing.T) {
	if got := CappedXP(100, "production:complete", 0, 0, 0); got != 100 {
		t.Fatal(got)
	}
	if got := CappedXP(100, "production:complete", 20, 0, 0); got != 50 {
		t.Fatal(got)
	}
	if got := CappedXP(100, "production:complete", 100, 0, 0); got != 25 {
		t.Fatal(got)
	}
	if got := CappedXP(100, "production:complete", 0, 249990, 0); got != 10 {
		t.Fatal(got)
	}
	if got := CappedXP(1, "forest:chop", 100, 0, 0); got != 0 {
		t.Fatal(got)
	}
	if got := CappedXP(500, "building:destroy", 0, 0, 2000000); got != 0 {
		t.Fatal(got)
	}
}
