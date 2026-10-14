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
	r.buildings[b.ID] = b
	return nil
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
