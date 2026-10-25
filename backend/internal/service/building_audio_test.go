package service

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
)

func TestCompletionReasonDistinguishesUpgradeFromPlacement(t *testing.T) {
	now := time.Now()
	item := building.Building{CreatedAt: now, StartedAt: now}
	if got := completionReason(item); got != "completed" {
		t.Fatalf("initial construction: got %q", got)
	}
	item.StartedAt = now.Add(time.Minute)
	if got := completionReason(item); got != "upgrade_completed" {
		t.Fatalf("upgrade construction: got %q", got)
	}
}
