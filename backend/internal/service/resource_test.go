package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

func TestResourceServicePublishesResourceChunk(t *testing.T) {
	repo := memory.NewEconomyRepo()
	economyService := NewEconomyService(repo, nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewResourceService(repo, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	bus := NewEventBus(1)
	service.SetEventBus(bus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	events := bus.Subscribe(ctx)

	node, err := service.Claim(ctx, economy.NodeID("node_oil_2"), player.ID("p1"))
	if err != nil {
		t.Fatalf("claim node: %v", err)
	}
	if node.Tile.X != 91 || node.Tile.Y != 73 {
		t.Fatalf("unexpected fixture tile: %#v", node.Tile)
	}

	select {
	case event := <-events:
		if event.Type != EventResourceChanged {
			t.Fatalf("event type = %q", event.Type)
		}
		if event.ChunkID != "dev-world:2:2" {
			t.Fatalf("chunk id = %q", event.ChunkID)
		}
		if event.PlayerID != player.ID("p1") {
			t.Fatalf("player id = %q", event.PlayerID)
		}
	case <-time.After(time.Second):
		t.Fatal("expected resource event")
	}
}
