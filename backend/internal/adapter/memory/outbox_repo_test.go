package memory

import (
	"context"
	"testing"
	"time"

	outbox "real-city/backend/internal/domain/event"
)

func TestPruneSentKeepsPendingAndDeadEvents(t *testing.T) {
	ctx := context.Background()
	repo := NewOutboxRepo()
	now := time.Now().UTC()
	for _, id := range []outbox.ID{"sent", "pending", "dead"} {
		if err := repo.Append(ctx, outbox.NewOutboxEvent(id, "test", "", []byte(`{}`), now)); err != nil {
			t.Fatal(err)
		}
	}
	if err := repo.MarkSent(ctx, "sent", now); err != nil {
		t.Fatal(err)
	}
	if err := repo.MarkDead(ctx, "dead", "bad payload", now); err != nil {
		t.Fatal(err)
	}
	if count, err := repo.PruneSent(ctx, now.Add(time.Minute), 10); err != nil || count != 1 {
		t.Fatalf("prune count=%d err=%v", count, err)
	}
	if _, ok := repo.events["sent"]; ok {
		t.Fatal("sent event remains")
	}
	if _, ok := repo.events["pending"]; !ok {
		t.Fatal("pending event removed")
	}
	if _, ok := repo.events["dead"]; !ok {
		t.Fatal("dead event removed")
	}
}
