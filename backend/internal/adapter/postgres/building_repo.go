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

func (r *BuildingRepo) Create(ctx context.Context, b building.Building) (resultErr error) {
	defer observe("building.insert", time.Now(), &resultErr)
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO buildings (
			id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at,
			cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
	`, b.ID, b.MapID, b.OwnerID, b.Type, b.Name, b.Level, b.State, b.Health, b.Tile.X, b.Tile.Y, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.FieldStage, b.FieldStageStartedAt, b.FieldStageReadyAt, b.FieldSuperCrop, b.CreatedAt, b.UpdatedAt, b.CannonEnabled, b.CannonNextAttackAt, b.CannonTargetID, b.TrapCharges, b.Rotation)
	return err
}

func (r *BuildingRepo) FindByID(ctx context.Context, id building.ID) (building.Building, error) {
	query := `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
		FROM buildings
		WHERE id = $1
 `
	if _, ok := ctx.Value(txKey{}).(*sql.Tx); ok {
		query += ` FOR UPDATE`
	}
	row := execer(ctx, r.db).QueryRowContext(ctx, query, id)
	return scanBuilding(row)
}

func (r *BuildingRepo) ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
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

func (r *BuildingRepo) PlayerPlacementStats(ctx context.Context, playerID player.ID) (result building.PlacementStats, resultErr error) {
	defer observe("building.player_placement_stats", time.Now(), &resultErr)
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT
			COALESCE(MAX(CASE WHEN type = $2 AND state <> $3 THEN level ELSE 0 END), 0) AS town_hall_level,
			COUNT(*) FILTER (
				WHERE state <> $3
				  AND type NOT IN ($4, $5, $6, $7, $8, $9, $10, $11, $12)
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
		building.TypeDefenseStakes,
		building.TypeDefenseResinSnare,
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
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
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

func (r *BuildingRepo) ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) (items []building.Building, resultErr error) {
	defer observe("building.viewport_list", time.Now(), &resultErr)
	return r.listByViewport(ctx, mapID, minX, minY, maxX, maxY)
}

func (r *BuildingRepo) ListIntersectingFootprint(ctx context.Context, mapID string, minX, minY, maxX, maxY int) (items []building.Building, resultErr error) {
	defer observe("building.footprint_intersection", time.Now(), &resultErr)
	return r.listByViewport(ctx, mapID, minX, minY, maxX, maxY)
}

func (r *BuildingRepo) listByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
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
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
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

func (r *BuildingRepo) ListRuinedRuins(ctx context.Context, limit int) ([]building.Building, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
		FROM buildings WHERE state = 'ruined' AND type LIKE 'ruins_%'
		ORDER BY updated_at, id LIMIT $1
	`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) ListReadyCannons(ctx context.Context, mapID string, now time.Time, afterID building.ID, limit int) ([]building.Building, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y,
			footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at,
			field_stage_ready_at, field_super_crop, created_at, updated_at, cannon_enabled, cannon_next_attack_at, cannon_target_id, trap_charges, rotation
		FROM buildings
		WHERE map_id = $1 AND type IN ($2, 'defense_bolt_thrower', 'defense_storm_coil') AND state IN ($3, $6) AND cannon_enabled = TRUE AND id > $7
			AND (cannon_next_attack_at IS NULL OR cannon_next_attack_at <= $4)
		ORDER BY id LIMIT $5
	`, mapID, building.TypeDefenseCannon, building.StateActive, now, limit, building.StateDamaged, afterID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanBuildings(rows)
}

func (r *BuildingRepo) ClaimCannonShot(ctx context.Context, id building.ID, now, next time.Time, targetID string, expectedHealth int) (bool, error) {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings SET cannon_next_attack_at = $2, cannon_target_id = $3, updated_at = $4
		WHERE id = $1 AND type IN ($5, 'defense_bolt_thrower', 'defense_storm_coil') AND state IN ($6, $7) AND cannon_enabled = TRUE AND health = $8
			AND (cannon_next_attack_at IS NULL OR cannon_next_attack_at <= $4)
	`, id, next, targetID, now, building.TypeDefenseCannon, building.StateActive, building.StateDamaged, expectedHealth)
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
}

func (r *BuildingRepo) ConsumeTrapCharge(ctx context.Context, id building.ID, expectedHealth int) (bool, error) {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings SET trap_charges = trap_charges - 1, updated_at = now()
		WHERE id = $1 AND type IN ('defense_stakes', 'defense_resin_snare')
		  AND state IN ('active', 'damaged') AND trap_charges > 0 AND health = $2
	`, id, expectedHealth)
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
}

func (r *BuildingRepo) DamageIfCurrent(ctx context.Context, id building.ID, expectedHealth, damage int, now time.Time, expectedOwner ...string) (building.Building, bool, error) {
	if damage <= 0 {
		return building.Building{}, false, nil
	}
	owner := ""
	if len(expectedOwner) > 0 {
		owner = expectedOwner[0]
	}
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings
		SET health = GREATEST(0, health - $3),
			state = CASE WHEN health <= $3 THEN $4 WHEN state IN ($8, $10) THEN state ELSE $5 END,
			cannon_enabled = CASE WHEN health <= $3 THEN false ELSE cannon_enabled END,
			updated_at = $6
		WHERE id = $1 AND health = $2 AND health > 0 AND state IN ($7, $5, $8, $10) AND ($9 = '' OR owner_id = $9)
	`, id, expectedHealth, damage, building.StateRuined, building.StateDamaged, now, building.StateActive, building.StateBuilding, owner, building.StateRepairing)
	if err != nil {
		return building.Building{}, false, err
	}
	affected, err := result.RowsAffected()
	if err != nil || affected == 0 {
		return building.Building{}, false, err
	}
	item, err := r.FindByID(ctx, id)
	return item, err == nil, err
}

func (r *BuildingRepo) Update(ctx context.Context, b building.Building) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings
		SET type = $2, name = $3, level = $4, state = $5, health = $6,
			footprint_w = $7, footprint_h = $8, started_at = $9, completes_at = $10,
			field_stage = $11, field_stage_started_at = $12, field_stage_ready_at = $13,
			field_super_crop = $14, updated_at = $15,
			cannon_enabled = $16, cannon_next_attack_at = $17, cannon_target_id = $18, trap_charges = $19, rotation = $20
		WHERE id = $1 AND (state <> 'ruined' OR $5 = 'ruined')
	`, b.ID, b.Type, b.Name, b.Level, b.State, b.Health, b.Footprint.Width, b.Footprint.Height, b.StartedAt, b.CompletesAt, b.FieldStage, b.FieldStageStartedAt, b.FieldStageReadyAt, b.FieldSuperCrop, b.UpdatedAt, b.CannonEnabled, b.CannonNextAttackAt, b.CannonTargetID, b.TrapCharges, b.Rotation)
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

func (r *BuildingRepo) RelocateIfCurrent(ctx context.Context, previous, next building.Building) (bool, error) {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE buildings AS target
		SET tile_x = $2, tile_y = $3, footprint_w = $4, footprint_h = $5,
			rotation = $6, updated_at = $7
		WHERE target.id = $1 AND target.tile_x = $8 AND target.tile_y = $9
			AND target.rotation = $10 AND target.updated_at = $11 AND target.state = $14
			AND NOT EXISTS (
				SELECT 1 FROM buildings AS occupied
				WHERE occupied.map_id = target.map_id AND occupied.id <> target.id
					AND occupied.state <> 'ruined'
					AND NOT (($12 AND occupied.type IN ('road', 'standard_road', 'paved_road'))
						OR ($13 AND occupied.type IN ('defense_stakes', 'defense_resin_snare')))
					AND EXISTS (
						SELECT 1 FROM generate_series(-1, 1) AS sx, generate_series(-1, 1) AS sy
						WHERE occupied.tile_x + sx * $15::integer < $2::integer + $4::integer
							AND occupied.tile_x + sx * $15::integer + GREATEST(occupied.footprint_w, 1) > $2::integer
							AND occupied.tile_y + sy * $15::integer < $3::integer + $5::integer
							AND occupied.tile_y + sy * $15::integer + GREATEST(occupied.footprint_h, 1) > $3::integer
						)
			)
	`, previous.ID, next.Tile.X, next.Tile.Y, next.Footprint.Width, next.Footprint.Height,
		next.Rotation, next.UpdatedAt, previous.Tile.X, previous.Tile.Y, previous.Rotation,
		previous.UpdatedAt, building.IsTrapType(next.Type), building.IsRoadType(next.Type), previous.State, world.WorldSize)
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
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
		&item.CannonEnabled,
		&item.CannonNextAttackAt,
		&item.CannonTargetID,
		&item.TrapCharges,
		&item.Rotation,
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
