package service

import (
	"context"
	"fmt"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type RepairCost struct {
	Resource economy.ResourceType `json:"resource"`
	Amount   int                  `json:"amount"`
}
type RepairQuote struct {
	Cost            []RepairCost        `json:"cost"`
	Workers         int                 `json:"workers"`
	DurationSeconds int                 `json:"duration_seconds"`
	Job             *building.RepairJob `json:"job,omitempty"`
}

func (s *BuildingService) SetRepairUnitOfWork(u UnitOfWork) { s.repairUOW = u }
func (s *BuildingService) repairTransaction(ctx context.Context, fn func(context.Context) error) error {
	u := s.repairUOW
	if u == nil {
		repos := []any{s.buildings}
		if s.economy != nil {
			repos = append(repos, s.economy.repo)
		}
		u = snapshotUnitOfWork{repos}
	}
	return transactional(ctx, u, fn)
}
func (s *BuildingService) RepairStatus(ctx context.Context, id building.ID, p player.ID) (RepairQuote, error) {
	b, err := s.requireOwned(ctx, id, p)
	if err != nil {
		return RepairQuote{}, err
	}
	quote := quoteRepair(b)
	duration, err := s.buffedDuration(ctx, p, time.Duration(quote.DurationSeconds)*time.Second, "repair_speed")
	if err != nil {
		return quote, err
	}
	quote.DurationSeconds = max(1, int(duration/time.Second))
	if repo, ok := s.buildings.(RepairRepository); ok {
		job, e := repo.PendingRepair(ctx, id)
		if e == nil {
			quote.Job = &job
		} else if !isNotFound(e) {
			return quote, e
		}
	}
	return quote, nil
}

// Quarter of the level's construction materials, proportional to missing HP;
// one worker, half of proportional build time, at least five seconds.
func quoteRepair(b building.Building) RepairQuote {
	spec, _ := catalog.GetBuilding(b.Type)
	cost := spec.Cost
	duration := spec.BuildDuration
	for _, v := range spec.UpgradeLevels {
		if v.Level == b.Level {
			cost = v.Cost
			duration = v.BuildDuration
			break
		}
	}
	hp := buildingHealthForLevel(b.Type, b.Level)
	missing := max(0, hp-b.Health)
	quote := RepairQuote{Cost: []RepairCost{}, Workers: 1, DurationSeconds: max(5, int(duration.Seconds())*missing/max(1, hp)/2)}
	for _, v := range cost {
		if v.Amount > 0 && v.Resource != "population" {
			amount := max(1, (v.Amount*missing+4*hp-1)/max(1, 4*hp))
			quote.Cost = append(quote.Cost, RepairCost{Resource: economy.ResourceType(v.Resource), Amount: amount})
		}
	}
	return quote
}
func (s *BuildingService) Repair(ctx context.Context, id building.ID, p player.ID) (result building.Building, err error) {
	repo, ok := s.buildings.(RepairRepository)
	if !ok || s.economy == nil {
		return result, apperror.New(apperror.Conflict, "Ремонт временно недоступен")
	}
	err = s.repairTransaction(ctx, func(ctx context.Context) error {
		if err := lockBuilding(ctx, s.buildings, id); err != nil {
			return err
		}
		b, e := s.requireOwned(ctx, id, p)
		if e != nil {
			return e
		}
		if b.State != building.StateActive && b.State != building.StateDamaged {
			return apperror.New(apperror.Conflict, "Ремонтировать можно только завершённую, не разрушенную постройку")
		}
		if b.Health >= buildingHealthForLevel(b.Type, b.Level) {
			return apperror.New(apperror.Conflict, "Постройка не нуждается в ремонте")
		}
		if _, e = repo.PendingRepair(ctx, id); e == nil {
			return apperror.New(apperror.Conflict, "Ремонт уже выполняется")
		} else if !isNotFound(e) {
			return e
		}
		quote := quoteRepair(b)
		duration, e := s.buffedDuration(ctx, p, time.Duration(quote.DurationSeconds)*time.Second, "repair_speed")
		if e != nil {
			return e
		}
		quote.DurationSeconds = max(1, int(duration/time.Second))
		cost := []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: quote.Workers}}
		for _, v := range quote.Cost {
			cost = append(cost, economy.ResourceAmount{Resource: v.Resource, Amount: v.Amount})
		}
		if _, e = s.economy.Spend(WithoutCatchUp(ctx), p, cost, "repair:reserve"); e != nil {
			return e
		}
		now := s.now()
		dueAt := now.Add(time.Duration(quote.DurationSeconds) * time.Second)
		job := building.RepairJob{ID: fmt.Sprintf("repair_%s_%d", id, now.UnixNano()), BuildingID: id, PlayerID: string(p), BuildingType: b.Type, Level: b.Level, Workers: quote.Workers, DueAt: dueAt, Status: "pending"}
		if e = repo.CreateRepair(ctx, job); e != nil {
			return e
		}
		b.State = building.StateRepairing
		b.CompletesAt = &dueAt
		b.UpdatedAt = now
		if e = s.buildings.Update(ctx, b); e != nil {
			return e
		}
		publishEvent(ctx, s.events, Event{Type: EventBuildingUpdated, PlayerID: p, ChunkID: world.ChunkID(b.MapID, world.ChunkForTile(b.Tile)), Payload: BuildingPayload{Building: b, Reason: "repair_started"}})
		result = b
		return nil
	})
	return
}
func (s *BuildingService) CompleteRepairs(ctx context.Context, now time.Time, limit int) (int, error) {
	repo, ok := s.buildings.(RepairRepository)
	if !ok || s.economy == nil {
		return 0, nil
	}
	jobs, err := repo.DueRepairs(ctx, now, limit)
	if err != nil {
		return 0, err
	}
	done := 0
	for _, candidate := range jobs {
		err = s.repairTransaction(ctx, func(ctx context.Context) error {
			if err := lockBuilding(ctx, s.buildings, candidate.BuildingID); err != nil && !isNotFound(err) {
				return err
			}
			job, e := repo.LockRepair(ctx, candidate.ID)
			if e != nil {
				return e
			}
			if job.Status != "pending" || job.DueAt.After(now) {
				return nil
			}
			b, e := s.buildings.FindByID(ctx, job.BuildingID)
			if e != nil && !isNotFound(e) {
				return e
			}
			status := "cancelled"
			if e == nil && b.OwnerID == job.PlayerID && b.Type == job.BuildingType && b.Level == job.Level && b.Health > 0 && (b.State == building.StateRepairing || b.State == building.StateActive || b.State == building.StateDamaged) {
				b.Health = buildingHealthForLevel(b.Type, b.Level)
				b.State = building.StateActive
				b.CompletesAt = nil
				b.UpdatedAt = now
				if e = s.buildings.Update(ctx, b); e != nil {
					return e
				}
				status = "completed"
				publishEvent(ctx, s.events, Event{Type: EventBuildingUpdated, PlayerID: player.ID(job.PlayerID), ChunkID: world.ChunkID(b.MapID, world.ChunkForTile(b.Tile)), Payload: BuildingPayload{Building: b, Reason: "repaired"}})
			}
			if _, _, e = s.economy.Add(WithoutCatchUp(ctx), player.ID(job.PlayerID), []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: job.Workers}}, "repair:workers_returned"); e != nil {
				return e
			}
			if e = repo.FinishRepair(ctx, job.ID, status); e != nil {
				return e
			}
			s.log.Info("building.repair.finished", "event", "building.repair.finished", "building_id", job.BuildingID, "status", status)
			done++
			return nil
		})
		if err != nil {
			return done, err
		}
	}
	return done, nil
}
