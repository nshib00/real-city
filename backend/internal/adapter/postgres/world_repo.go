package postgres

import (
	"context"
	"database/sql"
	"errors"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type WorldRepo struct {
	db        *sql.DB
	generator worldgen.Generator
}

func NewWorldRepo(db *sql.DB) *WorldRepo {
	return &WorldRepo{
		db:        db,
		generator: worldgen.New("dev-world", 20260727, 10),
	}
}

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

func (r *WorldRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, bool, error) {
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

func (r *WorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords {
		chunk, _, err := r.GetOrCreateChunk(ctx, mapID, coord)
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

func (r *WorldRepo) findChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, error) {
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
		SELECT tile_x, tile_y, terrain, elevation, safe_zone, forest_density
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
		if err := rows.Scan(&tile.Coord.X, &tile.Coord.Y, &tile.Terrain, &tile.Elevation, &tile.SafeZone, &tile.ForestDensity); err != nil {
			return world.Chunk{}, err
		}
		chunk.Tiles = append(chunk.Tiles, tile)
	}
	return chunk, rows.Err()
}

func (r *WorldRepo) createChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, error) {
	if err := r.ensureMap(ctx); err != nil {
		return world.Chunk{}, err
	}
	chunk := r.generator.Chunk(coord)
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return world.Chunk{}, err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback()
		}
	}()

	_, err = tx.ExecContext(ctx, `
		INSERT INTO world_chunks (map_id, chunk_x, chunk_y, version)
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (map_id, chunk_x, chunk_y) DO NOTHING
	`, mapID, coord.X, coord.Y, chunk.Version)
	if err != nil {
		return world.Chunk{}, err
	}
	for _, tile := range chunk.Tiles {
		_, err = tx.ExecContext(ctx, `
			INSERT INTO world_tiles (
				map_id, tile_x, tile_y, chunk_x, chunk_y, terrain, elevation, safe_zone, forest_density
			)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
			ON CONFLICT (map_id, tile_x, tile_y) DO NOTHING
		`, mapID, tile.Coord.X, tile.Coord.Y, coord.X, coord.Y, tile.Terrain, tile.Elevation, tile.SafeZone, tile.ForestDensity)
		if err != nil {
			return world.Chunk{}, err
		}
	}
	if err = tx.Commit(); err != nil {
		return world.Chunk{}, err
	}
	return r.findChunk(ctx, mapID, coord)
}

func (r *WorldRepo) UpdateTile(ctx context.Context, tile world.Tile) error {
	result, err := r.db.ExecContext(ctx, `
		UPDATE world_tiles
		SET terrain = $4, elevation = $5, safe_zone = $6, forest_density = $7, updated_at = now()
		WHERE map_id = $1 AND tile_x = $2 AND tile_y = $3
	`, tile.MapID, tile.Coord.X, tile.Coord.Y, tile.Terrain, tile.Elevation, tile.SafeZone, tile.ForestDensity)
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
	return err
}
