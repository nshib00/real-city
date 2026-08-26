package dto

import "real-city/backend/internal/domain/world"

type WorldMapResponse struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Seed        int64  `json:"seed"`
	ChunkSize   int    `json:"chunk_size"`
	SpawnRadius int    `json:"spawn_radius"`
}

type ChunkResponse struct {
	MapID   string         `json:"map_id"`
	ChunkX  int            `json:"chunk_x"`
	ChunkY  int            `json:"chunk_y"`
	Version int64          `json:"version"`
	Tiles   []TileResponse `json:"tiles"`
}

type TileResponse struct {
	X             int    `json:"x"`
	Y             int    `json:"y"`
	ChunkX        int    `json:"chunk_x"`
	ChunkY        int    `json:"chunk_y"`
	Terrain       string `json:"terrain"`
	Elevation     int    `json:"elevation"`
	SafeZone      bool   `json:"safe_zone"`
	ForestDensity int    `json:"forest_density"`
}

type ChopForestRequest struct {
	TileX int `json:"tile_x"`
	TileY int `json:"tile_y"`
}

func WorldMap(worldMap world.WorldMap) WorldMapResponse {
	return WorldMapResponse{
		ID:          worldMap.ID,
		Name:        worldMap.Name,
		Seed:        worldMap.Seed,
		ChunkSize:   worldMap.ChunkSize,
		SpawnRadius: worldMap.SpawnRadius,
	}
}

func Chunk(chunk world.Chunk) ChunkResponse {
	tiles := make([]TileResponse, 0, len(chunk.Tiles))
	for _, tile := range chunk.Tiles {
		tiles = append(tiles, Tile(tile))
	}
	return ChunkResponse{
		MapID:   chunk.MapID,
		ChunkX:  chunk.Coord.X,
		ChunkY:  chunk.Coord.Y,
		Version: chunk.Version,
		Tiles:   tiles,
	}
}

func Chunks(chunks []world.Chunk) []ChunkResponse {
	responses := make([]ChunkResponse, 0, len(chunks))
	for _, chunk := range chunks {
		responses = append(responses, Chunk(chunk))
	}
	return responses
}

func Tile(tile world.Tile) TileResponse {
	return TileResponse{
		X:             tile.Coord.X,
		Y:             tile.Coord.Y,
		ChunkX:        tile.Chunk.X,
		ChunkY:        tile.Chunk.Y,
		Terrain:       string(tile.Terrain),
		Elevation:     tile.Elevation,
		SafeZone:      tile.SafeZone,
		ForestDensity: tile.ForestDensity,
	}
}
