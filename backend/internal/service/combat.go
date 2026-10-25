package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type CombatService struct {
	monsters *MonsterService
	economy  EconomyRepository
	actions  ActionRepository
	uow      UnitOfWork
	log      *slog.Logger
	now      func() time.Time
	mu       sync.Mutex
}

type WeaponAttack struct {
	ID      action.ID            `json:"id"`
	Weapon  economy.ResourceType `json:"weapon"`
	DueAt   time.Time            `json:"due_at"`
	Monster *monster.Monster     `json:"-"`
	Loot    *monster.LootDrop    `json:"-"`
}

type PendingWeaponAttack struct {
	ID        action.ID            `json:"id"`
	MonsterID monster.ID           `json:"monster_id"`
	Weapon    economy.ResourceType `json:"weapon"`
	DueAt     time.Time            `json:"due_at"`
}

func NewCombatService(monsters *MonsterService, log *slog.Logger) *CombatService {
	return &CombatService{monsters: monsters, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *CombatService) SetWeaponDependencies(economyRepo EconomyRepository, actions ActionRepository, uow UnitOfWork) {
	s.economy, s.actions, s.uow = economyRepo, actions, uow
}

func (s *CombatService) PendingWeapons(ctx context.Context, playerID player.ID) ([]PendingWeaponAttack, error) {
	if s.actions == nil {
		return []PendingWeaponAttack{}, nil
	}
	actions, err := s.actions.ListPendingWeapons(ctx, playerID)
	if err != nil {
		return nil, err
	}
	items := make([]PendingWeaponAttack, 0, len(actions))
	for _, item := range actions {
		var payload struct {
			Weapon economy.ResourceType `json:"weapon"`
		}
		if err := json.Unmarshal(item.Payload, &payload); err != nil {
			continue
		}
		items = append(items, PendingWeaponAttack{ID: item.ID, MonsterID: monster.ID(item.Target.ID), Weapon: payload.Weapon, DueAt: item.DueAt})
	}
	return items, nil
}

func (s *CombatService) UseWeapon(ctx context.Context, id monster.ID, playerID player.ID, resource economy.ResourceType, key string) (WeaponAttack, error) {
	spec, ok := catalog.PlayerWeaponByResource(resource)
	if !ok {
		return WeaponAttack{}, apperror.New(apperror.Validation, "unknown weapon")
	}
	if len(key) < 8 || len(key) > 128 {
		return WeaponAttack{}, apperror.New(apperror.Validation, "Idempotency-Key must contain 8 to 128 characters")
	}
	if s.economy == nil || s.actions == nil {
		return WeaponAttack{}, apperror.New(apperror.Conflict, "weapons are unavailable")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	used, err := s.actions.HasIdempotencyKey(ctx, "weapon:"+string(playerID)+":"+key)
	if err != nil {
		return WeaponAttack{}, err
	}
	if used {
		return WeaponAttack{}, apperror.New(apperror.Conflict, "weapon action already submitted")
	}
	now := s.now()
	target, err := s.monsters.Get(ctx, id)
	if err != nil {
		return WeaponAttack{}, err
	}
	if !target.Alive() {
		return WeaponAttack{}, apperror.New(apperror.Conflict, "monster is already dead")
	}
	attack := WeaponAttack{ID: action.ID(fmt.Sprintf("weapon_%d_%s", now.UnixNano(), playerID)), Weapon: resource, DueAt: now.Add(spec.Fuse)}
	item := action.NewGameAction(attack.ID, action.TypeDetonateWeapon, "weapon:"+string(playerID)+":"+key,
		action.ObjectRef{ID: string(playerID), Type: "player"}, action.ObjectRef{ID: string(id), Type: "monster"}, attack.DueAt, now)
	item.Payload, _ = json.Marshal(struct {
		Weapon economy.ResourceType `json:"weapon"`
	}{resource})
	run := func(ctx context.Context) error {
		spent, err := s.economy.SpendResourceIfAvailable(ctx, playerID, resource, 1, now)
		if err != nil {
			return err
		}
		if !spent {
			return apperror.New(apperror.Conflict, "weapon is not available in inventory")
		}
		created, err := s.actions.AppendUnique(ctx, item)
		if err != nil {
			return err
		}
		if !created {
			return apperror.New(apperror.Conflict, "weapon action already submitted")
		}
		if spec.Fuse == 0 {
			resolved, loot, err := s.monsters.Damage(ctx, id, playerID, weaponDamage(spec, target.Type))
			if err != nil {
				return err
			}
			attack.Monster, attack.Loot = &resolved, loot
			return s.actions.MarkDone(ctx, item.ID, now)
		}
		return nil
	}
	if s.uow != nil {
		err = s.uow.Do(ctx, run)
	} else {
		err = run(ctx)
	}
	if err != nil {
		return WeaponAttack{}, err
	}
	s.log.Info("combat.weapon.used", "player_id", playerID, "monster_id", id, "weapon", resource, "due_at", attack.DueAt)
	return attack, nil
}

func (s *CombatService) ResolveWeapon(ctx context.Context, item action.GameAction) error {
	var payload struct {
		Weapon economy.ResourceType `json:"weapon"`
	}
	if err := json.Unmarshal(item.Payload, &payload); err != nil {
		return err
	}
	spec, ok := catalog.PlayerWeaponByResource(payload.Weapon)
	if !ok {
		return apperror.New(apperror.Validation, "unknown queued weapon")
	}
	target, err := s.monsters.Get(ctx, monster.ID(item.Target.ID))
	if err != nil {
		return err
	}
	if !target.Alive() {
		return nil
	}
	_, _, err = s.monsters.Damage(ctx, target.ID, player.ID(item.Actor.ID), weaponDamage(spec, target.Type))
	return err
}

func weaponDamage(spec catalog.PlayerWeaponSpec, kind monster.Type) int {
	if kind == monster.TypeAncientColossus {
		return spec.ColossusDamage
	}
	return spec.Damage
}
