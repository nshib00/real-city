package postgres

import (
	"context"
	"database/sql"
	"errors"
	"sync"
	"time"

	"github.com/lib/pq"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type WorldRepo struct {
	db        *sql.DB
	generator worldgen.Generator
	mu        sync.RWMutex
	cache     map[worldChunkCacheKey]world.Chunk
}

func NewWorldRepo(db *sql.DB) *WorldRepo {
	return &WorldRepo{
		db:        db,
		generator: worldgen.New("dev-world", 20260727, 10),
		cache:     make(map[worldChunkCacheKey]world.Chunk),
	}
}

type worldChunkCacheKey struct {
	mapID string
	coord world.ChunkCoord
}

const worldChunkCacheMaxEntries = 1024

func (r *WorldRepo) GetMap(ctx context.Context, id string) (world.WorldMap, error) {
	if err := r.ensureMap(ctx); err != nil {
		return world.WorldMap{}, err
	}
	row := r.db.QueryRowContext(ctx, `
		SELECT id, name, seed, chunk_size, spawn_radius
		FROM world_maps
		WHERE id = $1
	`, id)
	var worldMap world.WorldMap
	err := row.Scan(&worldMap.ID, &worldMap.Name, &worldMap.Seed, &worldMap.ChunkSize, &worldMap.SpawnRadius)
	if errors.Is(err, sql.ErrNoRows) {
		return world.WorldMap{}, apperror.New(apperror.NotFound, "world map not found")
	}
	return worldMap, err
}

func (r *WorldRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (chunkResult world.Chunk, cached bool, resultErr error) {
	started := time.Now()
	defer func() { observability.ObserveWorld("world.get_or_create_chunk", started, resultErr) }()
	if chunk, ok := r.cachedChunk(mapID, coord); ok {
		observability.CacheLookup(true)
		return chunk, true, nil
	}
	observability.CacheLookup(false)
	chunk, err := r.findChunk(ctx, mapID, coord)
	if err == nil {
		return chunk, true, nil
	}
	var appErr *apperror.Error
	if !errors.As(err, &appErr) || appErr.Kind != apperror.NotFound {
		return world.Chunk{}, false, err
	}
	chunk, err = r.createChunk(ctx, mapID, coord)
	return chunk, false, err
}

func (r *WorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) (result []world.Chunk, resultErr error) {
	started := time.Now()
	defer func() { observability.ObserveWorld("world.get_or_create_chunks", started, resultErr) }()
	if len(coords) == 0 {
		return []world.Chunk{}, nil
	}
	chunksByCoord := make(map[world.ChunkCoord]world.Chunk, len(coords))
	missing := make([]world.ChunkCoord, 0, len(coords))
	for _, coord := range coords {
		if chunk, ok := r.cachedChunk(mapID, coord); ok {
			observability.CacheLookup(true)
			chunksByCoord[coord] = chunk
			continue
		}
		observability.CacheLookup(false)
		missing = append(missing, coord)
	}
	if len(missing) == 0 {
		chunks := make([]world.Chunk, 0, len(coords))
		for _, coord := range coords {
			chunks = append(chunks, chunksByCoord[coord])
		}
		return chunks, nil
	}
	if err := r.ensureMap(ctx); err != nil {
		return nil, err
	}
	existing, err := r.findChunks(ctx, mapID, missing)
	if err != nil {
		return nil, err
	}
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords {
		if chunk, ok := chunksByCoord[coord]; ok {
			chunks = append(chunks, chunk)
			continue
		}
		if chunk, ok := existing[coord]; ok {
			chunks = append(chunks, chunk)
			continue
		}
		chunk, err := r.createChunk(ctx, mapID, coord)
		if err != nil {
			return nil, err
		}
		chunks = append(chunks, chunk)
	}
	return chunks, nil
}

func (r *WorldRepo) GetOrCreateChunksFresh(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	if len(coords) == 0 {
		return []world.Chunk{}, nil
	}
	if err := r.ensureMap(ctx); err != nil {
		return nil, err
	}
	existing, err := r.findChunks(ctx, mapID, coords)
	if err != nil {
		return nil, err
	}
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords {
		if chunk, ok := existing[coord]; ok {
			chunks = append(chunks, chunk)
			continue
		}
		chunk, err := r.createChunk(ctx, mapID, coord)
		if err != nil {
			return nil, err
		}
		chunks = append(chunks, chunk)
	}
	return chunks, nil
}

func (r *WorldRepo) ensureMap(ctx context.Context) error {
	worldMap := r.generator.Map()
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO world_maps (id, name, seed, chunk_size, spawn_radius)
		VALUES ($1, $2, $3, $4, $5)
		ON CONFLICT (id) DO NOTHING
	`, worldMap.ID, worldMap.Name, worldMap.Seed, worldMap.ChunkSize, worldMap.SpawnRadius)
	return err
}

func (r *WorldRepo) findChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (found world.Chunk, resultErr error) {
	defer observe("world.find_chunk", time.Now(), &resultErr)
	if err := r.ensureMap(ctx); err != nil {
		return world.Chunk{}, err
	}
	row := r.db.QueryRowContext(ctx, `
		SELECT version
		FROM world_chunks
		WHERE map_id = $1 AND chunk_x = $2 AND chunk_y = $3
	`, mapID, coord.X, coord.Y)
	chunk := world.Chunk{MapID: mapID, Coord: coord}
	if err := row.Scan(&chunk.Version); errors.Is(err, sql.ErrNoRows) {
		return world.Chunk{}, apperror.New(apperror.NotFound, "world chunk not found")
	} else if err != nil {
		return world.Chunk{}, err
	}

	rows, err := r.db.QueryContext(ctx, `
		SELECT tile_x, tile_y, terrain, ruin_type, elevation, safe_zone, forest_density
		FROM world_tiles
		WHERE map_id = $1 AND chunk_x = $2 AND chunk_y = $3
		ORDER BY tile_y, tile_x
	`, mapID, coord.X, coord.Y)
	if err != nil {
		return world.Chunk{}, err
	}
	defer rows.Close()

	for rows.Next() {
		tile := world.Tile{MapID: mapID, Chunk: coord}
		if err := rows.Scan(&tile.Coord.X, &tile.Coord.Y, &tile.Terrain, &tile.RuinType, &tile.Elevation, &tile.SafeZone, &tile.ForestDensity); err != nil {
			return world.Chunk{}, err
		}
		chunk.Tiles = append(chunk.Tiles, tile)
	}
	if err := rows.Err(); err != nil {
		return world.Chunk{}, err
	}
	r.storeChunk(chunk)
	return cloneChunk(chunk), nil
}

func (r *WorldRepo) findChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) (result map[world.ChunkCoord]world.Chunk, resultErr error) {
	defer observe("world.find_chunks", time.Now(), &resultErr)
	minX, maxX, minY, maxY := coords[0].X, coords[0].X, coords[0].Y, coords[0].Y
	wanted := make(map[world.ChunkCoord]bool, len(coords))
	for _, coord := range coords {
		wanted[coord] = true
		if coord.X < minX {
			minX = coord.X
		}
		if coord.X > maxX {
			maxX = coord.X
		}
		if coord.Y < minY {
			minY = coord.Y
		}
		if coord.Y > maxY {
			maxY = coord.Y
		}
	}
	rows, err := r.db.QueryContext(ctx, `
		SELECT chunk_x, chunk_y, version
		FROM world_chunks
		WHERE map_id = $1
		  AND chunk_x BETWEEN $2 AND $3
		  AND chunk_y BETWEEN $4 AND $5
	`, mapID, minX, maxX, minY, maxY)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	chunks := make(map[world.ChunkCoord]world.Chunk, len(coords))
	for rows.Next() {
		var coord world.ChunkCoord
		var version int64
		if err := rows.Scan(&coord.X, &coord.Y, &version); err != nil {
			return nil, err
		}
		if !wanted[coord] {
			continue
		}
		chunks[coord] = world.Chunk{MapID: mapID, Coord: coord, Version: version}
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	if len(chunks) == 0 {
		return chunks, nil
	}

	tileRows, err := r.db.QueryContext(ctx, `
		SELECT chunk_x, chunk_y, tile_x, tile_y, terrain, ruin_type, elevation, safe_zone, forest_density
		FROM world_tiles
		WHERE map_id = $1
		  AND chunk_x BETWEEN $2 AND $3
		  AND chunk_y BETWEEN $4 AND $5
		ORDER BY chunk_y, chunk_x, tile_y, tile_x
	`, mapID, minX, maxX, minY, maxY)
	if err != nil {
		return nil, err
	}
	defer tileRows.Close()

	for tileRows.Next() {
		var tile world.Tile
		if err := tileRows.Scan(&tile.Chunk.X, &tile.Chunk.Y, &tile.Coord.X, &tile.Coord.Y, &tile.Terrain, &tile.RuinType, &tile.Elevation, &tile.SafeZone, &tile.ForestDensity); err != nil {
			return nil, err
		}
		chunk, ok := chunks[tile.Chunk]
		if !ok {
			continue
		}
		tile.MapID = mapID
		chunk.Tiles = append(chunk.Tiles, tile)
		chunks[tile.Chunk] = chunk
	}
	if err := tileRows.Err(); err != nil {
		return nil, err
	}
	for _, chunk := range chunks {
		r.storeChunk(chunk)
	}
	return cloneChunkMap(chunks), nil
}

func (r *WorldRepo) createChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (created world.Chunk, resultErr error) {
	started := time.Now()
	defer func() { observability.ObserveWorld("world.create_chunk", started, resultErr) }()
	if err := r.ensureMap(ctx); err != nil {
		return world.Chunk{}, err
	}
	generationStarted := time.Now()
	chunk := r.generator.Chunk(coord)
	observability.ObserveWorld("world.generate_chunk", generationStarted, nil)
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return world.Chunk{}, err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback()
		}
	}()

	result, err := tx.ExecContext(ctx, `
		INSERT INTO world_chunks (map_id, chunk_x, chunk_y, version)
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (map_id, chunk_x, chunk_y) DO NOTHING
	`, mapID, coord.X, coord.Y, chunk.Version)
	if err != nil {
		return world.Chunk{}, err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return world.Chunk{}, err
	}
	if affected == 0 {
		if err = tx.Commit(); err != nil {
			return world.Chunk{}, err
		}
		return r.findChunk(ctx, mapID, coord)
	}
	copyStarted := time.Now()
	defer func() { observability.ObserveDB("world.copy_tiles", copyStarted, resultErr) }()
	stmt, err := tx.Prepare(pq.CopyIn("world_tiles", "map_id", "tile_x", "tile_y", "chunk_x", "chunk_y", "terrain", "ruin_type", "elevation", "safe_zone", "forest_density"))
	if err != nil {
		return world.Chunk{}, err
	}
	for _, tile := range chunk.Tiles {
		if _, err = stmt.Exec(mapID, tile.Coord.X, tile.Coord.Y, coord.X, coord.Y, tile.Terrain, tile.RuinType, tile.Elevation, tile.SafeZone, tile.ForestDensity); err != nil {
			_ = stmt.Close()
			return world.Chunk{}, err
		}
	}
	if _, err = stmt.Exec(); err != nil {
		_ = stmt.Close()
		return world.Chunk{}, err
	}
	if err = stmt.Close(); err != nil {
		return world.Chunk{}, err
	}
	if err = tx.Commit(); err != nil {
		return world.Chunk{}, err
	}
	observability.ChunkCreated()
	r.storeChunk(chunk)
	return cloneChunk(chunk), nil
}

func (r *WorldRepo) UpdateTile(ctx context.Context, tile world.Tile) (resultErr error) {
	defer observe("world.update_tile", time.Now(), &resultErr)
	result, err := r.db.ExecContext(ctx, `
		UPDATE world_tiles
		SET terrain = $4, ruin_type = $5, elevation = $6, safe_zone = $7, forest_density = $8, updated_at = now()
		WHERE map_id = $1 AND tile_x = $2 AND tile_y = $3
	`, tile.MapID, tile.Coord.X, tile.Coord.Y, tile.Terrain, tile.RuinType, tile.Elevation, tile.SafeZone, tile.ForestDensity)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected == 0 {
		return apperror.New(apperror.NotFound, "world tile not found")
	}
	_, err = r.db.ExecContext(ctx, `
		UPDATE world_chunks
		SET version = version + 1, updated_at = now()
		WHERE map_id = $1 AND chunk_x = $2 AND chunk_y = $3
	`, tile.MapID, tile.Chunk.X, tile.Chunk.Y)
	if err != nil {
		return err
	}
	r.patchCachedTile(tile)
	return nil
}

func (r *WorldRepo) cachedChunk(mapID string, coord world.ChunkCoord) (world.Chunk, bool) {
	r.mu.RLock()
	chunk, ok := r.cache[worldChunkCacheKey{mapID: mapID, coord: coord}]
	r.mu.RUnlock()
	if !ok {
		return world.Chunk{}, false
	}
	return cloneChunk(chunk), true
}

func (r *WorldRepo) storeChunk(chunk world.Chunk) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(r.cache) >= worldChunkCacheMaxEntries {
		r.cache = make(map[worldChunkCacheKey]world.Chunk)
	}
	r.cache[worldChunkCacheKey{mapID: chunk.MapID, coord: chunk.Coord}] = cloneChunk(chunk)
	observability.SetCacheEntries(len(r.cache))
}

func (r *WorldRepo) patchCachedTile(tile world.Tile) {
	r.mu.Lock()
	defer r.mu.Unlock()
	key := worldChunkCacheKey{mapID: tile.MapID, coord: tile.Chunk}
	chunk, ok := r.cache[key]
	if !ok {
		return
	}
	chunk.Version++
	for index, current := range chunk.Tiles {
		if current.Coord == tile.Coord {
			chunk.Tiles[index] = tile
			r.cache[key] = chunk
			return
		}
	}
	chunk.Tiles = append(chunk.Tiles, tile)
	r.cache[key] = chunk
}

func cloneChunk(chunk world.Chunk) world.Chunk {
	chunk.Tiles = append([]world.Tile(nil), chunk.Tiles...)
	return chunk
}

func cloneChunkMap(chunks map[world.ChunkCoord]world.Chunk) map[world.ChunkCoord]world.Chunk {
	cloned := make(map[world.ChunkCoord]world.Chunk, len(chunks))
	for coord, chunk := range chunks {
		cloned[coord] = cloneChunk(chunk)
	}
	return cloned
}
