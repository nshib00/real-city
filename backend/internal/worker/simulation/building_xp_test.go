package simulation

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

type failingMonsterXPRepo struct {
	*memory.PlayerRepo
	fail bool
}

type failingWeaponAckRepo struct {
	*memory.ActionRepo
	fail bool
}

func (r *failingWeaponAckRepo) MarkDone(ctx context.Context, id action.ID, now time.Time) error {
	if err := r.ActionRepo.MarkDone(ctx, id, now); err != nil {
		return err
	}
	if r.fail {
		return errors.New("injected queue acknowledgement failure")
	}
	return nil
}

func TestQueuedLethalWeaponRollsBackDamageAndXPWhenAcknowledgementFails(t *testing.T) {
	ctx, now := context.Background(), time.Now().UTC()
	players, buildings := memory.NewPlayerRepo(), memory.NewBuildingRepo()
	if err := players.Create(ctx, player.Player{ID: "attacker", Email: "attacker@example.com", Name: "attacker", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	target := building.Building{ID: "enemy", OwnerID: "enemy", Type: building.TypeModernWall, Level: 13, State: building.StateActive, Health: 1}
	if err := buildings.Create(ctx, target); err != nil {
		t.Fatal(err)
	}
	bs := service.NewBuildingService(buildings, nil, slog.Default())
	bs.SetExperience(service.NewExperienceService(players, slog.Default()))
	actions := &failingWeaponAckRepo{ActionRepo: memory.NewActionRepo(), fail: true}
	combat := service.NewCombatService(service.NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
	combat.SetBuildingService(bs)
	combat.SetPvPDependencies(buildings, nil, nil)
	runner := &Runner{actions: actions, buildings: bs, combat: combat}
	hit := action.NewGameAction("queued", action.TypeDetonateWeapon, "queued", action.ObjectRef{ID: "attacker", Type: "player"}, action.ObjectRef{ID: "enemy", Type: "building"}, now, now)
	hit.Payload = []byte(`{"owner_id":"enemy","weapon":"blackpowder_bomb"}`)
	if err := actions.Append(ctx, hit); err != nil {
		t.Fatal(err)
	}
	if err := runner.handleAction(ctx, hit, now); err == nil {
		t.Fatal("expected acknowledgement failure")
	}
	unchanged, _ := buildings.FindByID(ctx, target.ID)
	profile, _ := players.FindByID(ctx, "attacker")
	if unchanged.Health != 1 || profile.Profile.XP != 0 {
		t.Fatal("failed queue transaction leaked damage or XP")
	}
	due, err := actions.FetchDue(ctx, now, 10, time.Minute)
	if err != nil || len(due) != 1 {
		t.Fatalf("failed action is not retryable: %+v %v", due, err)
	}
	actions.fail = false
	for range 2 {
		if err := runner.handleAction(ctx, hit, now); err != nil {
			t.Fatal(err)
		}
	}
	profile, _ = players.FindByID(ctx, "attacker")
	if profile.Profile.XP != 493817 {
		t.Fatalf("XP %d, want 493817", profile.Profile.XP)
	}
	due, err = actions.FetchDue(ctx, now.Add(2*time.Minute), 10, time.Minute)
	if err != nil || len(due) != 0 {
		t.Fatal("completed weapon remained in queue")
	}
}

func TestQueuedCompletionsIgnoreRemovedBuildingsAndJobs(t *testing.T) {
	buildings, inventory := memory.NewBuildingRepo(), memory.NewEconomyRepo()
	runner := &Runner{
		buildings:  service.NewBuildingService(buildings, nil, slog.Default()),
		production: service.NewProductionService(inventory, service.NewEconomyService(inventory, buildings, slog.Default()), slog.Default()),
	}
	for _, kind := range []action.Type{action.TypeCompleteBuilding, action.TypeCompleteProduction} {
		item := action.GameAction{Type: kind, Actor: action.ObjectRef{ID: "owner"}, Target: action.ObjectRef{ID: "removed"}}
		if err := runner.handleAction(context.Background(), item, time.Now()); err != nil {
			t.Fatal(err)
		}
	}
}

func (r *failingMonsterXPRepo) AwardXPEvent(ctx context.Context, id player.ID, amount int, reason, key string) (bool, error) {
	applied, err := r.PlayerRepo.AwardXPEvent(ctx, id, amount, reason, key)
	if err == nil && r.fail {
		return false, errors.New("injected XP failure")
	}
	return applied, err
}

func TestMonsterDestructionAwardsCreatorAndRollsBackFailedXP(t *testing.T) {
	for _, kind := range []building.Type{building.TypeDugout, building.TypeModernWall, building.TypeOilWell, "ruins_archive"} {
		for _, creator := range []string{"creator", ""} {
			t.Run(fmt.Sprintf("%s/creator=%s", kind, creator), func(t *testing.T) {
				ctx, now := context.Background(), time.Now().UTC()
				players := &failingMonsterXPRepo{PlayerRepo: memory.NewPlayerRepo(), fail: creator != ""}
				if err := players.Create(ctx, player.Player{ID: "creator", Email: "c@example.com", Name: "creator", Status: player.StatusActive, Profile: player.DefaultProfile("creator", now)}); err != nil {
					t.Fatal(err)
				}
				monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
				seeds, _ := monsters.ListByMap(ctx, service.DefaultWorldID)
				for _, seed := range seeds {
					seed.Health, seed.State = 0, monster.StateDead
					if err := monsters.Update(ctx, seed); err != nil {
						t.Fatal(err)
					}
				}
				level := 1
				if kind == building.TypeModernWall {
					level = 13
				}
				target := building.Building{ID: "enemy", OwnerID: "enemy", MapID: service.DefaultWorldID, Type: kind, Level: level, State: building.StateActive, Health: 1, Tile: world.Coord{X: 5, Y: 5}, Footprint: building.Footprint{Width: 1, Height: 1}}
				if err := buildings.Create(ctx, target); err != nil {
					t.Fatal(err)
				}
				item := monster.Monster{ID: "killer", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee, CreatorID: creator, ExpiresAt: now.Add(time.Hour), Tile: world.Coord{X: 5, Y: 6}, HomeTile: world.Coord{X: 5, Y: 6}, State: monster.StateAggro, Health: 100, MaxHealth: 100, Damage: 10, AggroRadius: 5, AttackRange: 1, AttackCooldown: time.Second}
				if err := monsters.Create(ctx, item); err != nil {
					t.Fatal(err)
				}
				xp := service.NewExperienceService(players, slog.Default())
				bs := service.NewBuildingService(buildings, nil, slog.Default())
				bs.SetExperience(xp)
				ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
				ai.SetBuildingService(bs)
				if creator != "" {
					if _, err := ai.Tick(ctx, now, 10); err == nil {
						t.Fatal("expected XP failure")
					}
					unchanged, err := buildings.FindByID(ctx, target.ID)
					if err != nil || unchanged.Health != 1 {
						t.Fatal("lethal hit was not rolled back")
					}
					unchangedMonster, _ := monsters.FindByID(ctx, item.ID)
					if !unchangedMonster.NextAttackAt.Equal(item.NextAttackAt) {
						t.Fatal("monster attack was not rolled back")
					}
					profile, _ := players.FindByID(ctx, "creator")
					if profile.Profile.XP != 0 {
						t.Fatal("failed transaction leaked XP")
					}
					players.fail = false
				}
				if _, err := ai.Tick(ctx, now, 10); err != nil {
					t.Fatal(err)
				}
				if _, err := ai.Tick(ctx, now, 10); err != nil {
					t.Fatal(err)
				}
				profile, _ := players.FindByID(ctx, "creator")
				want := 0
				if creator != "" {
					want = catalog.ExperienceForBuilding(kind, level).Destruction
				}
				if profile.Profile.XP != want {
					t.Fatalf("XP %d, want %d", profile.Profile.XP, want)
				}
				if kind == building.TypeOilWell || catalog.IsRuin(kind) {
					if _, err := buildings.FindByID(ctx, target.ID); err == nil {
						t.Fatal("destroyed special building still exists")
					}
				} else {
					destroyed, _ := buildings.FindByID(ctx, target.ID)
					if destroyed.State != building.StateRuined {
						t.Fatal("building survived lethal hit")
					}
				}
			})
		}
	}
}
