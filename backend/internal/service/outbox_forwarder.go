package service

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"time"

	outbox "real-city/backend/internal/domain/event"
)

// NewOutboxForwarder persists standalone-worker events for delivery by the API.
func NewOutboxForwarder(repo OutboxRepository) func(Event) error {
	return func(event Event) error {
		payload, err := json.Marshal(event.Payload)
		if err != nil {
			return err
		}
		var randomID [16]byte
		if _, err := rand.Read(randomID[:]); err != nil {
			return err
		}
		item := outbox.NewOutboxEvent(outbox.ID(hex.EncodeToString(randomID[:])), string(event.Type), "", payload, event.CreatedAt)
		item.ChunkID = event.ChunkID
		item.PlayerID = string(event.PlayerID)
		item.Alliance = event.Alliance
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		return repo.Append(ctx, item)
	}
}
