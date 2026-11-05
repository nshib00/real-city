package service

import "real-city/backend/internal/domain/world"

func chunkCacheKey(mapID string, coord world.ChunkCoord) string {
	coord = world.NormalizeChunk(coord)
	return "real-city:cache:chunk:" + world.ChunkID(mapID, coord)
}
