package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type BuildingRepo struct {
	db *sql.DB
}

func NewBuildingRepo(db *sql.DB) *BuildingRepo {
	return &BuildingRepo{db: db}
}

func (r *BuildingRepo) Create(ctx context.Context, b building.Building) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO buildings (
			id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
	`, b.ID, b.MapID, b.OwnerID, b.Type, b.Name, b.Level, b.State, b.Health, b.Tile.X, b.Tile.Y, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.FieldStage, b.FieldStageStartedAt, b.FieldStageReadyAt, b.FieldSuperCrop, b.CreatedAt, b.UpdatedAt)
	return err
}

func (r *BuildingRepo) FindByID(ctx context.Context, id building.ID) (building.Building, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`, id)
	return scanBuilding(row)
}

func (r *BuildingRepo) ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		FROM buildings
		WHERE owner_id = $1
		ORDER BY created_at, id
	`, playerID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) PlayerPlacementStats(ctx context.Context, playerID player.ID) (building.PlacementStats, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT
			COALESCE(MAX(CASE WHEN type = $2 AND state <> $3 THEN level ELSE 0 END), 0) AS town_hall_level,
			COUNT(*) FILTER (
				WHERE state <> $3
				  AND type NOT IN ($4, $5, $6, $7, $8, $9, $10)
			) AS used_limit
		FROM buildings
		WHERE owner_id = $1
	`, playerID,
		building.TypeTownHall,
		building.StateRuined,
		building.TypeRoad,
		building.TypeStandardRoad,
		building.TypePavedRoad,
		building.TypeWoodenWall,
		building.TypeStoneWall,
		building.TypeConcreteWall,
		building.TypeModernWall,
	)
	var stats building.PlacementStats
	if err := row.Scan(&stats.TownHallLevel, &stats.UsedLimit); err != nil {
		return building.PlacementStats{}, err
	}
	stats.HasTownHall = stats.TownHallLevel > 0
	return stats, nil
}

func (r *BuildingRepo) ListByMap(ctx context.Context, mapID string) ([]building.Building, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		FROM buildings
		WHERE map_id = $1
		ORDER BY created_at, id
	`, mapID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) ListByChunk(ctx context.Context, mapID string, coord world.ChunkCoord) ([]building.Building, error) {
	origin := world.ChunkOrigin(coord)
	return r.listByViewport(ctx, mapID, origin.X, origin.Y, origin.X+world.ChunkSize-1, origin.Y+world.ChunkSize-1)
}

func (r *BuildingRepo) ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	return r.listByViewport(ctx, mapID, minX, minY, maxX, maxY)
}

func (r *BuildingRepo) ListIntersectingFootprint(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	return r.listByViewport(ctx, mapID, minX, minY, maxX, maxY)
}

func (r *BuildingRepo) listByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		FROM buildings
		WHERE map_id = $1
		  AND tile_x <= $4
		  AND tile_x + GREATEST(footprint_w, 1) - 1 >= $2
		  AND tile_y <= $5
		  AND tile_y + GREATEST(footprint_h, 1) - 1 >= $3
		ORDER BY tile_y, tile_x, created_at
	`, mapID, minX, minY, maxX, maxY)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) ListDue(ctx context.Context, now time.Time, limit int) ([]building.Building, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at
		FROM buildings
		WHERE state = $1 AND completes_at IS NOT NULL AND completes_at <= $2
		ORDER BY completes_at, id
		LIMIT $3
	`, building.StateBuilding, now, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) Update(ctx context.Context, b building.Building) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings
		SET type = $2, name = $3, level = $4, state = $5, health = $6,
			footprint_w = $7, footprint_h = $8, started_at = $9, completes_at = $10,
			field_stage = $11, field_stage_started_at = $12, field_stage_ready_at = $13,
			field_super_crop = $14, updated_at = $15
		WHERE id = $1
	`, b.ID, b.Type, b.Name, b.Level, b.State, b.Health, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.FieldStage, b.FieldStageStartedAt, b.FieldStageReadyAt, b.FieldSuperCrop, b.UpdatedAt)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected == 0 {
		return apperror.New(apperror.NotFound, "building not found")
	}
	return nil
}

func (r *BuildingRepo) Delete(ctx context.Context, id building.ID) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `DELETE FROM buildings WHERE id = $1`, id)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected == 0 {
		return apperror.New(apperror.NotFound, "building not found")
	}
	return nil
}

type scanner interface {
	Scan(dest ...any) error
}

func scanBuilding(row scanner) (building.Building, error) {
	var item building.Building
	err := row.Scan(
		&item.ID,
		&item.MapID,
		&item.OwnerID,
		&item.Type,
		&item.Name,
		&item.Level,
		&item.State,
		&item.Health,
		&item.Tile.X,
		&item.Tile.Y,
		&item.Footprint.Width,
		&item.Footprint.Height,
		&item.StartedAt,
		&item.CompletesAt,
		&item.FieldStage,
		&item.FieldStageStartedAt,
		&item.FieldStageReadyAt,
		&item.FieldSuperCrop,
		&item.CreatedAt,
		&item.UpdatedAt,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return building.Building{}, apperror.New(apperror.NotFound, "building not found")
	}
	return item, err
}

func scanBuildings(rows *sql.Rows) ([]building.Building, error) {
	items := make([]building.Building, 0)
	for rows.Next() {
		item, err := scanBuilding(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}
