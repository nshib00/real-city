package service

import (
	"context"
	"errors"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
)

func TestCombatHistoryIsPrivateIdempotentAndRollsBack(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewActionRepo()
	s := NewBuildingService(memory.NewBuildingRepo(), nil, slog.Default())
	s.SetActionQueue(repo)
	players := memory.NewPlayerRepo()
	if err := players.Create(ctx, player.Player{ID: "attacker", Name: "Attacker", Email: "attacker@example.invalid", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	xp := NewExperienceService(players, slog.Default())
	s.SetExperience(xp)
	bus := NewEventBus(16)
	s.SetEventBus(bus)
	stream := bus.Subscribe(ctx)
	before := building.Building{ID: "victim", OwnerID: "owner", Type: building.TypeDugout, Level: 1, Health: 10, State: building.StateActive}
	after := before
	after.Health = 0
	after.State = building.StateRuined
	record := func(ctx context.Context) error {
		if err := xp.Award(ctx, "attacker", catalog.ExperienceForBuilding(before.Type, 1).Destruction, "building:destroy", "building:victim:destroy"); err != nil {
			return err
		}
		return s.RecordBuildingAttack(ctx, before, after, "attacker", "player_weapon", "attack-1", time.Now().UTC())
	}
	if err := s.DestructionTransaction(ctx, nil, func(ctx context.Context) error {
		if err := record(ctx); err != nil {
			return err
		}
		return errors.New("queue acknowledgement failed")
	}); err == nil {
		t.Fatal("expected rollback")
	}
	rows, _ := repo.ListCombatRecords(ctx, "owner", 50)
	if len(rows) != 0 {
		t.Fatal("rolled-back hit in history")
	}
	select {
	case <-stream:
		t.Fatal("rolled-back notification published")
	default:
	}
	if err := s.DestructionTransaction(ctx, nil, record); err != nil {
		t.Fatal(err)
	}
	if err := s.DestructionTransaction(ctx, nil, record); err != nil {
		t.Fatal(err)
	}
	combat := NewCombatService(nil, slog.Default())
	combat.SetWeaponDependencies(nil, repo, nil)
	for _, id := range []player.ID{"owner", "attacker"} {
		rows, err := combat.History(ctx, id, 50)
		if err != nil || len(rows) != 1 || rows[0].XP != catalog.ExperienceForBuilding(before.Type, 1).Destruction {
			t.Fatalf("history %s: %+v %v", id, rows, err)
		}
	}
	outsiderRows, err := combat.History(ctx, "outsider", 50)
	if err != nil || len(outsiderRows) != 0 {
		t.Fatal("outsider read history")
	}
	for i := 0; i < 2; i++ {
		select {
		case event := <-stream:
			if event.PlayerID != "owner" && event.PlayerID != "attacker" {
				t.Fatal("notification leaked")
			}
		default:
			t.Fatal("missing notification")
		}
	}
	select {
	case <-stream:
		t.Fatal("duplicate notification")
	default:
	}
}
