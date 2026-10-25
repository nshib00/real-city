package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type BuildingRepo struct {
	mu        sync.RWMutex
	buildings map[building.ID]building.Building
}

func NewBuildingRepo() *BuildingRepo {
	return &BuildingRepo{buildings: make(map[building.ID]building.Building)}
}

func (r *BuildingRepo) Create(ctx context.Context, b building.Building) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.buildings[b.ID]; ok {
		return apperror.New(apperror.Conflict, "building already exists")
	}
	if (b.Type == building.TypeOilWell || isRuinType(b.Type)) && b.State != building.StateRuined {
		for _, existing := range r.buildings {
			if existing.MapID == b.MapID && existing.Tile == b.Tile && existing.Type == b.Type && existing.State != building.StateRuined {
				return apperror.New(apperror.Conflict, "клетка уже занята")
			}
		}
	}
	r.buildings[b.ID] = b
	return nil
}

func isRuinType(kind building.Type) bool { return len(kind) > 6 && string(kind[:6]) == "ruins_" }

func (r *BuildingRepo) ListRuinedRuins(ctx context.Context, limit int) ([]building.Building, error) {
	items, err := r.ListByMap(ctx, "dev-world")
	if err != nil {
		return nil, err
	}
	result := make([]building.Building, 0)
	for _, item := range items {
		if isRuinType(item.Type) && item.State == building.StateRuined {
			result = append(result, item)
		}
		if limit > 0 && len(result) >= limit {
			break
		}
	}
	return result, nil
}

func (r *BuildingRepo) FindByID(ctx context.Context, id building.ID) (building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.buildings[id]
	if !ok {
		return building.Building{}, apperror.New(apperror.NotFound, "building not found")
	}
	return item, nil
}

func (r *BuildingRepo) ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]building.Building, 0)
	for _, item := range r.buildings {
		if item.OwnerID == string(playerID) {
			items = append(items, item)
		}
	}
	return items, nil
}

func (r *BuildingRepo) PlayerPlacementStats(ctx context.Context, playerID player.ID) (building.PlacementStats, error) {
	items, err := r.ListByPlayer(ctx, playerID)
	if err != nil {
		return building.PlacementStats{}, err
	}
	stats := building.PlacementStats{
		HasTownHall:   building.HasTownHall(items),
		TownHallLevel: townHallLevel(items),
		UsedLimit:     building.UsedBuildingLimit(items),
	}
	return stats, nil
}

func (r *BuildingRepo) ListByMap(ctx context.Context, mapID string) ([]building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]building.Building, 0)
	for _, item := range r.buildings {
		if item.MapID == mapID {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.Before(items[j].CreatedAt) })
	return items, nil
}

func (r *BuildingRepo) ListByChunk(ctx context.Context, mapID string, coord world.ChunkCoord) ([]building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]building.Building, 0)
	for _, item := range r.buildings {
		if item.MapID == mapID && world.ChunkForTile(item.Tile) == coord {
			items = append(items, item)
		}
	}
	return items, nil
}

func (r *BuildingRepo) ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]building.Building, 0)
	for _, item := range r.buildings {
		if item.MapID != mapID {
			continue
		}
		right := item.Tile.X + max(1, item.Footprint.Width) - 1
		bottom := item.Tile.Y + max(1, item.Footprint.Height) - 1
		if right < minX || item.Tile.X > maxX || bottom < minY || item.Tile.Y > maxY {
			continue
		}
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].Tile.Y == items[j].Tile.Y {
			return items[i].Tile.X < items[j].Tile.X
		}
		return items[i].Tile.Y < items[j].Tile.Y
	})
	return items, nil
}

func (r *BuildingRepo) ListIntersectingFootprint(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	return r.ListByViewport(ctx, mapID, minX, minY, maxX, maxY)
}

func townHallLevel(items []building.Building) int {
	level := 0
	for _, item := range items {
		if item.Type == building.TypeTownHall && item.State != building.StateRuined && item.Level > level {
			level = item.Level
		}
	}
	return level
}

func (r *BuildingRepo) ListDue(ctx context.Context, now time.Time, limit int) ([]building.Building, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]building.Building, 0)
	for _, item := range r.buildings {
		if item.State == building.StateBuilding && item.CompletesAt != nil && !item.CompletesAt.After(now) {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CompletesAt.Before(*items[j].CompletesAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *BuildingRepo) ListReadyCannons(ctx context.Context, mapID string, now time.Time, afterID building.ID, limit int) ([]building.Building, error) {
	items, err := r.ListByMap(ctx, mapID)
	if err != nil {
		return nil, err
	}
	ready := make([]building.Building, 0)
	for _, item := range items {
		if item.ID > afterID && (item.Type == building.TypeDefenseCannon || item.Type == building.TypeDefenseBoltThrower || item.Type == building.TypeDefenseStormCoil) && (item.State == building.StateActive || item.State == building.StateDamaged) && item.CannonEnabled &&
			(item.CannonNextAttackAt == nil || !item.CannonNextAttackAt.After(now)) {
			ready = append(ready, item)
		}
	}
	sort.Slice(ready, func(i, j int) bool { return ready[i].ID < ready[j].ID })
	if limit > 0 && len(ready) > limit {
		ready = ready[:limit]
	}
	return ready, nil
}

func (r *BuildingRepo) ClaimCannonShot(ctx context.Context, id building.ID, now, next time.Time, targetID string, expectedHealth int) (bool, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.buildings[id]
	if !ok || item.Health != expectedHealth || (item.Type != building.TypeDefenseCannon && item.Type != building.TypeDefenseBoltThrower && item.Type != building.TypeDefenseStormCoil) || (item.State != building.StateActive && item.State != building.StateDamaged) || !item.CannonEnabled ||
		(item.CannonNextAttackAt != nil && item.CannonNextAttackAt.After(now)) {
		return false, nil
	}
	item.CannonNextAttackAt = &next
	item.CannonTargetID = targetID
	item.UpdatedAt = now
	r.buildings[id] = item
	return true, nil
}

func (r *BuildingRepo) ConsumeTrapCharge(ctx context.Context, id building.ID, expectedHealth int) (bool, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.buildings[id]
	if !ok || !building.IsTrapType(item.Type) || (item.State != building.StateActive && item.State != building.StateDamaged) || item.TrapCharges < 1 || item.Health != expectedHealth {
		return false, nil
	}
	item.TrapCharges--
	r.buildings[id] = item
	return true, nil
}

func (r *BuildingRepo) DamageIfCurrent(ctx context.Context, id building.ID, expectedHealth, damage int, now time.Time) (building.Building, bool, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.buildings[id]
	if !ok || item.Health != expectedHealth || item.Health <= 0 || damage <= 0 || (item.State != building.StateActive && item.State != building.StateDamaged && item.State != building.StateBuilding) {
		return building.Building{}, false, nil
	}
	item.Health = max(0, item.Health-damage)
	if item.Health == 0 {
		item.State = building.StateRuined
		item.CannonEnabled = false
	} else if item.State != building.StateBuilding {
		item.State = building.StateDamaged
	}
	item.UpdatedAt = now
	r.buildings[id] = item
	return item, true, nil
}

func (r *BuildingRepo) Update(ctx context.Context, b building.Building) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.buildings[b.ID]; !ok {
		return apperror.New(apperror.NotFound, "building not found")
	}
	r.buildings[b.ID] = b
	return nil
}

func (r *BuildingRepo) RelocateIfCurrent(ctx context.Context, previous, next building.Building) (bool, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	current, ok := r.buildings[previous.ID]
	if !ok || current.Tile != previous.Tile || current.Rotation != previous.Rotation || current.State != previous.State || current.UpdatedAt != previous.UpdatedAt {
		return false, nil
	}
	for _, other := range r.buildings {
		if other.ID == previous.ID || other.MapID != previous.MapID || other.State == building.StateRuined ||
			(building.IsTrapType(next.Type) && building.IsRoadType(other.Type)) ||
			(building.IsRoadType(next.Type) && building.IsTrapType(other.Type)) {
			continue
		}
		for _, target := range next.OccupiedTiles() {
			for _, occupied := range other.OccupiedTiles() {
				if target == occupied {
					return false, nil
				}
			}
		}
	}
	r.buildings[next.ID] = next
	return true, nil
}

func (r *BuildingRepo) Delete(ctx context.Context, id building.ID) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.buildings[id]; !ok {
		return apperror.New(apperror.NotFound, "building not found")
	}
	delete(r.buildings, id)
	return nil
}
