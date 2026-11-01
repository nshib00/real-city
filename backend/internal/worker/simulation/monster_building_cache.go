package simulation

import (
	"context"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

// tickBuildingCache shares spatial reads between nearby monsters in one AI tick.
// Damage and trap effects still use fresh repository reads and conditional writes.
type tickBuildingCache struct {
	repo    service.BuildingRepository
	buckets map[buildingCacheKey][]building.Building
}

type buildingCacheKey struct {
	mapID string
	x, y  int
}

func newTickBuildingCache(repo service.BuildingRepository) *tickBuildingCache {
	return &tickBuildingCache{repo: repo, buckets: make(map[buildingCacheKey][]building.Building)}
}

func (c *tickBuildingCache) clear() {
	clear(c.buckets)
}

func (ai *MonsterAI) buildingsInRect(ctx context.Context, mapID string, minX, minY, maxX, maxY int, cache *tickBuildingCache) ([]building.Building, error) {
	if cache == nil {
		return ai.buildings.ListIntersectingFootprint(ctx, mapID, minX, minY, maxX, maxY)
	}
	return cache.listInRect(ctx, mapID, minX, minY, maxX, maxY)
}

func (c *tickBuildingCache) listInRect(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	items := make([]building.Building, 0)
	seen := make(map[building.ID]bool)
	for y := floorDiv(minY, world.ChunkSize); y <= floorDiv(maxY, world.ChunkSize); y++ {
		for x := floorDiv(minX, world.ChunkSize); x <= floorDiv(maxX, world.ChunkSize); x++ {
			key := buildingCacheKey{mapID: mapID, x: x, y: y}
			bucket, ok := c.buckets[key]
			if !ok {
				var err error
				bucket, err = c.repo.ListIntersectingFootprint(ctx, mapID,
					x*world.ChunkSize, y*world.ChunkSize,
					(x+1)*world.ChunkSize-1, (y+1)*world.ChunkSize-1)
				if err != nil {
					return nil, err
				}
				c.buckets[key] = bucket
			}
			for _, item := range bucket {
				if seen[item.ID] || item.Tile.X > maxX || item.Tile.Y > maxY ||
					item.Tile.X+max(1, item.Footprint.Width)-1 < minX ||
					item.Tile.Y+max(1, item.Footprint.Height)-1 < minY {
					continue
				}
				seen[item.ID] = true
				items = append(items, item)
			}
		}
	}
	return items, nil
}

func floorDiv(value, divisor int) int {
	quotient := value / divisor
	if value < 0 && value%divisor != 0 {
		quotient--
	}
	return quotient
}
