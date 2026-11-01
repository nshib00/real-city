package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

func (s *CombatService) SetPvPDependencies(buildings BuildingRepository, worlds WorldRepository, resources *ResourceService) {
	s.buildings, s.worlds, s.resources = buildings, worlds, resources
}

func (s *CombatService) validatePvPTarget(ctx context.Context, actor player.ID, id building.ID) (building.Building, error) {
	if s.buildings == nil {
		return building.Building{}, apperror.New(apperror.Conflict, "Атаки построек недоступны")
	}
	target, err := s.buildings.FindByID(ctx, id)
	if err != nil {
		return target, err
	}
	if target.OwnerID == "" || target.OwnerID == string(actor) {
		return target, apperror.New(apperror.Forbidden, "Выберите чужую постройку")
	}
	if target.Health <= 0 || (target.State != building.StateActive && target.State != building.StateDamaged) {
		return target, apperror.New(apperror.Conflict, "Цель недоступна для атаки")
	}
	if s.buildingService != nil {
		if err := s.buildingService.CheckPvPProtection(ctx, player.ID(target.OwnerID), s.now()); err != nil {
			return target, err
		}
	}
	owned, err := s.buildings.ListByPlayer(ctx, actor)
	if err != nil {
		return target, err
	}
	for _, source := range owned {
		if source.MapID != target.MapID || source.Health <= 0 || source.State != building.StateActive {
			continue
		}
		for _, from := range source.OccupiedTiles() {
			for _, to := range target.OccupiedTiles() {
				if wrappedTileDistance(from.X, to.X)+wrappedTileDistance(from.Y, to.Y) <= catalog.CombatRules().AttackRangeTiles {
					return target, nil
				}
			}
		}
	}
	return target, apperror.New(apperror.Forbidden, "Цель вне дальности ваших действующих построек")
}

func (s *CombatService) damageBuilding(ctx context.Context, item action.GameAction, damage int, now time.Time) (*building.Building, error) {
	var result *building.Building
	work := func(ctx context.Context) error {
		var err error
		result, err = s.damageBuildingAt(ctx, item, damage, now)
		return err
	}
	var err error
	if s.buildingService != nil {
		err = s.buildingService.DestructionTransaction(ctx, s.uow, work)
	} else {
		err = work(ctx)
	}
	return result, err
}

func (s *CombatService) damageBuildingAt(ctx context.Context, item action.GameAction, damage int, now time.Time) (*building.Building, error) {
	var payload struct {
		OwnerID string `json:"owner_id"`
	}
	if err := json.Unmarshal(item.Payload, &payload); err != nil {
		return nil, err
	}
	target, err := s.buildings.FindByID(ctx, building.ID(item.Target.ID))
	if err != nil {
		var appErr *apperror.Error
		if errors.As(err, &appErr) && appErr.Kind == apperror.NotFound {
			return nil, nil
		}
		return nil, err
	}
	// A charge never follows a sold building or damages its new owner.
	if target.OwnerID == "" || target.OwnerID != payload.OwnerID || target.OwnerID == item.Actor.ID || target.Health <= 0 || (target.State != building.StateActive && target.State != building.StateDamaged) {
		return nil, nil
	}
	if s.buildingService != nil {
		var e error
		damage, e = s.buildingService.ProtectedDamage(ctx, player.ID(target.OwnerID), damage)
		if e != nil {
			return nil, e
		}
	}
	if s.buildingService != nil {
		damage, err = s.buildingService.PvPDamage(ctx, target, player.ID(item.Actor.ID), damage, now)
		if err != nil {
			return nil, err
		}
		if damage <= 0 {
			return nil, nil
		}
	}
	damaged, applied, err := s.buildings.DamageIfCurrent(ctx, target.ID, target.Health, damage, now, target.OwnerID)
	if err != nil {
		return nil, err
	}
	if !applied {
		return nil, apperror.New(apperror.Conflict, "Цель изменилась одновременно с атакой")
	}
	if damaged.Type != target.Type || damaged.Level != target.Level {
		return nil, apperror.New(apperror.Conflict, "Цель улучшена одновременно с атакой")
	}
	removed := damaged.State == building.StateRuined && (damaged.Type == building.TypeOilWell || catalog.IsRuin(damaged.Type))
	if damaged.State == building.StateRuined && s.buildingService != nil {
		if err := s.buildingService.HandleDestruction(ctx, target, damaged, player.ID(item.Actor.ID), now); err != nil {
			return nil, err
		}
	} else if removed {
		if damaged.Type == building.TypeOilWell && s.resources != nil {
			if err := s.resources.CancelOilJobs(ctx, damaged); err != nil {
				return nil, err
			}
			if err := s.resources.ReleaseOilWell(ctx, damaged.Tile, damaged.OwnerID); err != nil {
				return nil, err
			}
		}
		if err := s.buildings.Delete(ctx, damaged.ID); err != nil {
			return nil, err
		}
	}
	if s.monsters.events != nil {
		event := Event{Type: EventBuildingUpdated, ChunkID: world.ChunkID(damaged.MapID, world.ChunkForTile(damaged.Tile)), PlayerID: player.ID(damaged.OwnerID), Payload: BuildingPayload{Building: damaged, Reason: "player_weapon", Damage: target.Health - damaged.Health}}
		if removed {
			event.Type = EventBuildingRemoved
			event.Payload = BuildingRemovedPayload{BuildingID: damaged.ID, Reason: "player_weapon", Damage: target.Health - damaged.Health, TileX: damaged.Tile.X, TileY: damaged.Tile.Y, BuildingType: damaged.Type}
		}
		publishEvent(ctx, s.monsters.events, event)
	}
	s.log.Info("combat.building.damaged", "event", "combat.building.damaged", "player_id", item.Actor.ID, "owner_id", damaged.OwnerID, "building_id", damaged.ID, "damage", target.Health-damaged.Health, "action_id", item.ID)
	if s.buildingService != nil {
		if err := s.buildingService.RecordBuildingAttack(ctx, target, damaged, player.ID(item.Actor.ID), "player_weapon", string(item.ID), now); err != nil {
			return nil, err
		}
	}
	return &damaged, nil
}

// CreateMonster uses a fixed, server-owned catalog entry; clients cannot choose stats or rewards.
func (s *CombatService) CreateMonster(ctx context.Context, actor player.ID, targetID building.ID, key string) (monster.Monster, error) {
	if len(key) < 8 || len(key) > 128 {
		return monster.Monster{}, apperror.New(apperror.Validation, "Idempotency-Key must contain 8 to 128 characters")
	}
	if s.actions == nil || s.economy == nil || s.worlds == nil {
		return monster.Monster{}, apperror.New(apperror.Conflict, "Создание монстров недоступно")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	now := s.now()
	rules := catalog.CombatRules()
	var created monster.Monster
	run := func(ctx context.Context) error {
		if err := s.actions.LockCombatActor(ctx, actor); err != nil {
			return err
		}
		used, err := s.actions.HasIdempotencyKey(ctx, "summon:"+string(actor)+":"+key)
		if err != nil {
			return err
		}
		if used {
			return apperror.New(apperror.Conflict, "Создание монстра уже запрошено")
		}
		target, err := s.validatePvPTarget(ctx, actor, targetID)
		if err != nil {
			return err
		}
		recent, err := s.actions.HasRecentAction(ctx, actor, action.TypeCreateMonster, now.Add(-time.Duration(rules.SummonCooldownSeconds)*time.Second))
		if err != nil {
			return err
		}
		if recent {
			return apperror.New(apperror.Conflict, "Подождите перед созданием следующего монстра")
		}
		items, err := s.monsters.repo.ListByMap(ctx, target.MapID)
		if err != nil {
			return err
		}
		alive := 0
		for _, item := range items {
			if item.CreatorID == string(actor) && item.Alive() && item.ExpiresAt.After(now) {
				alive++
			}
		}
		if alive >= rules.SummonMaxAlive {
			return apperror.New(apperror.Conflict, "Достигнут лимит созданных монстров")
		}
		tile, err := s.summonTile(ctx, target, items)
		if err != nil {
			return err
		}
		spec, _ := catalog.MonsterSpec(monster.TypeRoamingMelee)
		created = monster.Monster{ID: monster.ID(fmt.Sprintf("summoned_%s_%d", actor, now.UnixNano())), CreatorID: string(actor), ExpiresAt: now.Add(time.Duration(rules.SummonLifetimeSeconds) * time.Second), MapID: target.MapID, Type: spec.Type, State: monster.StateAggro, Tile: tile, HomeTile: tile, TargetID: string(target.ID), TargetType: "building", Health: spec.MaxHealth, MaxHealth: spec.MaxHealth, Damage: spec.Damage, SpeedTiles: spec.SpeedTiles, AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange, AttackCooldown: spec.AttackCooldown, NextAttackAt: now.Add(5 * time.Second), LastMovedAt: now.Add(5 * time.Second), CreatedAt: now, UpdatedAt: now}
		spent, err := s.economy.SpendResourceIfAvailable(ctx, actor, economy.ResourceCoins, rules.SummonCostCoins, now)
		if err != nil {
			return err
		}
		if !spent {
			return apperror.New(apperror.Conflict, "Недостаточно монет для создания монстра")
		}
		item := action.NewGameAction(action.ID(created.ID), action.TypeCreateMonster, "summon:"+string(actor)+":"+key, action.ObjectRef{ID: string(actor), Type: "player"}, action.ObjectRef{ID: string(created.ID), Type: "monster"}, now, now)
		item.Payload = []byte(`{}`)
		ok, err := s.actions.AppendUnique(ctx, item)
		if err != nil {
			return err
		}
		if !ok {
			return apperror.New(apperror.Conflict, "Создание монстра уже запрошено")
		}
		if err := s.monsters.repo.Create(ctx, created); err != nil {
			return err
		}
		return s.actions.MarkDone(ctx, item.ID, now)
	}
	var err error
	if s.uow != nil {
		err = s.uow.Do(ctx, run)
	} else {
		err = run(ctx)
	}
	if err != nil {
		return monster.Monster{}, err
	}
	s.monsters.publish(EventMonsterSpawned, created, "")
	s.log.Info("combat.monster.created", "event", "combat.monster.created", "player_id", actor, "monster_id", created.ID, "target_id", targetID)
	return created, nil
}

func (s *CombatService) summonTile(ctx context.Context, target building.Building, monsters []monster.Monster) (world.Coord, error) {
	for radius := 2; radius <= 4; radius++ {
		for _, offset := range []world.Coord{{X: radius}, {Y: radius}, {X: -radius}, {Y: -radius}} {
			tile := world.Coord{X: (target.Tile.X + offset.X + worldgen.WorldSizeTiles) % worldgen.WorldSizeTiles, Y: (target.Tile.Y + offset.Y + worldgen.WorldSizeTiles) % worldgen.WorldSizeTiles}
			chunk, _, err := s.worlds.GetOrCreateChunk(ctx, target.MapID, world.ChunkForTile(tile))
			if err != nil {
				return world.Coord{}, err
			}
			grass := false
			for _, t := range chunk.Tiles {
				if t.Coord == tile {
					grass = t.Terrain == world.TerrainGrass
					break
				}
			}
			if !grass {
				continue
			}
			occupied, err := s.buildings.ListIntersectingFootprint(ctx, target.MapID, tile.X, tile.Y, tile.X, tile.Y)
			if err != nil {
				return world.Coord{}, err
			}
			if len(occupied) != 0 {
				continue
			}
			blocked := false
			for _, m := range monsters {
				if m.Alive() && m.Tile == tile {
					blocked = true
					break
				}
			}
			if !blocked {
				return tile, nil
			}
		}
	}
	return world.Coord{}, apperror.New(apperror.Conflict, "Рядом с целью нет свободной клетки для монстра")
}
