package monster

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/world"
)

func TestStepTowardMovesBySpeed(t *testing.T) {
	next := StepToward(world.Coord{X: 0, Y: 0}, world.Coord{X: 3, Y: 1}, 2)
	if next != (world.Coord{X: 2, Y: 0}) {
		t.Fatalf("expected x-axis movement, got %+v", next)
	}
}

func TestMonsterDamageKillsAndSetsState(t *testing.T) {
	item := Monster{State: StateAggro, Health: 10}
	if killed := item.ApplyDamage(12, time.Now()); !killed {
		t.Fatal("expected monster to die")
	}
	if item.State != StateDead || item.Health != 0 {
		t.Fatalf("expected dead monster with zero health, got state=%s health=%d", item.State, item.Health)
	}
}
