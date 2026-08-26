package postgres

import (
	"context"
	"database/sql"
	"errors"

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
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO buildings (
			id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
	`, b.ID, b.MapID, b.OwnerID, b.Type, b.Name, b.Level, b.State, b.Health, b.Tile.X, b.Tile.Y, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.CreatedAt, b.UpdatedAt)
	return err
}

func (r *BuildingRepo) FindByID(ctx context.Context, id building.ID) (building.Building, error) {
	row := r.db.QueryRowContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`, id)
	return scanBuilding(row)
}

func (r *BuildingRepo) ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, created_at, updated_at
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

func (r *BuildingRepo) ListByChunk(ctx context.Context, mapID string, coord world.ChunkCoord) ([]building.Building, error) {
	origin := world.ChunkOrigin(coord)
	rows, err := r.db.QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, created_at, updated_at
		FROM buildings
		WHERE map_id = $1
		  AND tile_x >= $2 AND tile_x < $3
		  AND tile_y >= $4 AND tile_y < $5
		ORDER BY tile_y, tile_x, created_at
	`, mapID, origin.X, origin.X+world.ChunkSize, origin.Y, origin.Y+world.ChunkSize)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) Update(ctx context.Context, b building.Building) error {
	result, err := r.db.ExecContext(ctx, `
		UPDATE buildings
		SET type = $2, name = $3, level = $4, state = $5, health = $6,
			footprint_w = $7, footprint_h = $8, started_at = $9, completes_at = $10, updated_at = $11
		WHERE id = $1
	`, b.ID, b.Type, b.Name, b.Level, b.State, b.Health, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.UpdatedAt)
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
	result, err := r.db.ExecContext(ctx, `DELETE FROM buildings WHERE id = $1`, id)
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
