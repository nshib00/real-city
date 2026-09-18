package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type MonsterRepo struct {
	db *sql.DB
}

func NewMonsterRepo(db *sql.DB) *MonsterRepo {
	return &MonsterRepo{db: db}
}

func (r *MonsterRepo) Create(ctx context.Context, item monster.Monster) error {
	return r.upsert(ctx, item)
}

func (r *MonsterRepo) FindByID(ctx context.Context, id monster.ID) (monster.Monster, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, monsterSelect()+` WHERE id = $1`, id)
	item, err := scanMonster(row)
	if errors.Is(err, sql.ErrNoRows) {
		return monster.Monster{}, apperror.New(apperror.NotFound, "monster not found")
	}
	return item, err
}

func (r *MonsterRepo) ListByMap(ctx context.Context, mapID string) ([]monster.Monster, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, monsterSelect()+` WHERE map_id = $1 AND state <> $2 ORDER BY id`, mapID, monster.StateDead)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanMonsters(rows)
}

func (r *MonsterRepo) ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.Monster, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, monsterSelect()+`
		WHERE map_id = $1 AND state <> $2 AND tile_x BETWEEN $3 AND $4 AND tile_y BETWEEN $5 AND $6
		ORDER BY id
	`, mapID, monster.StateDead, minX, maxX, minY, maxY)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanMonsters(rows)
}

func (r *MonsterRepo) Update(ctx context.Context, item monster.Monster) error {
	return r.upsert(ctx, item)
}

func (r *MonsterRepo) ListSpawnPoints(ctx context.Context, mapID string) ([]monster.SpawnPoint, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, type, tile_x, tile_y, radius, max_alive, cooldown_ms, next_spawn_at, created_at, updated_at
		FROM monster_spawn_points WHERE map_id = $1 ORDER BY id
	`, mapID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]monster.SpawnPoint, 0)
	for rows.Next() {
		var item monster.SpawnPoint
		var x, y int
		var cooldownMS int
		if err := rows.Scan(&item.ID, &item.MapID, &item.Type, &x, &y, &item.Radius, &item.MaxAlive, &cooldownMS, &item.NextSpawnAt, &item.CreatedAt, &item.UpdatedAt); err != nil {
			return nil, err
		}
		item.Tile = world.Coord{X: x, Y: y}
		item.Cooldown = time.Duration(cooldownMS) * time.Millisecond
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *MonsterRepo) SaveSpawnPoint(ctx context.Context, item monster.SpawnPoint) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO monster_spawn_points (id, map_id, type, tile_x, tile_y, radius, max_alive, cooldown_ms, next_spawn_at, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
		ON CONFLICT (id) DO UPDATE SET next_spawn_at = EXCLUDED.next_spawn_at, updated_at = EXCLUDED.updated_at
	`, item.ID, item.MapID, item.Type, item.Tile.X, item.Tile.Y, item.Radius, item.MaxAlive, int(item.Cooldown/time.Millisecond), item.NextSpawnAt, item.CreatedAt, item.UpdatedAt)
	return err
}

func (r *MonsterRepo) AddEvent(ctx context.Context, item monster.Event) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO monster_events (id, monster_id, type, target_id, tile_x, tile_y, created_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7)
	`, item.ID, item.MonsterID, item.Type, item.TargetID, item.Tile.X, item.Tile.Y, item.CreatedAt)
	return err
}

func (r *MonsterRepo) upsert(ctx context.Context, item monster.Monster) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO monsters (id, map_id, type, state, tile_x, tile_y, home_tile_x, home_tile_y, target_id, target_type, health, max_health, damage, speed_tiles, aggro_radius, attack_range, attack_cooldown_ms, next_attack_at, last_moved_at, loot_coins, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22)
		ON CONFLICT (id) DO UPDATE SET state = EXCLUDED.state, tile_x = EXCLUDED.tile_x, tile_y = EXCLUDED.tile_y, target_id = EXCLUDED.target_id, target_type = EXCLUDED.target_type, health = EXCLUDED.health, next_attack_at = EXCLUDED.next_attack_at, last_moved_at = EXCLUDED.last_moved_at, updated_at = EXCLUDED.updated_at
	`, item.ID, item.MapID, item.Type, item.State, item.Tile.X, item.Tile.Y, item.HomeTile.X, item.HomeTile.Y, item.TargetID, item.TargetType, item.Health, item.MaxHealth, item.Damage, item.SpeedTiles, item.AggroRadius, item.AttackRange, int(item.AttackCooldown/time.Millisecond), nullTime(item.NextAttackAt), item.LastMovedAt, item.LootCoins, item.CreatedAt, item.UpdatedAt)
	return err
}

func monsterSelect() string {
	return `SELECT id, map_id, type, state, tile_x, tile_y, home_tile_x, home_tile_y, target_id, target_type, health, max_health, damage, speed_tiles, aggro_radius, attack_range, attack_cooldown_ms, next_attack_at, last_moved_at, loot_coins, created_at, updated_at FROM monsters`
}

func scanMonsters(rows *sql.Rows) ([]monster.Monster, error) {
	items := make([]monster.Monster, 0)
	for rows.Next() {
		item, err := scanMonster(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

type monsterScanner interface{ Scan(dest ...any) error }

func scanMonster(row monsterScanner) (monster.Monster, error) {
	var item monster.Monster
	var tileX, tileY, homeX, homeY, cooldownMS int
	var nextAttack sql.NullTime
	if err := row.Scan(&item.ID, &item.MapID, &item.Type, &item.State, &tileX, &tileY, &homeX, &homeY, &item.TargetID, &item.TargetType, &item.Health, &item.MaxHealth, &item.Damage, &item.SpeedTiles, &item.AggroRadius, &item.AttackRange, &cooldownMS, &nextAttack, &item.LastMovedAt, &item.LootCoins, &item.CreatedAt, &item.UpdatedAt); err != nil {
		return monster.Monster{}, err
	}
	item.Tile = world.Coord{X: tileX, Y: tileY}
	item.HomeTile = world.Coord{X: homeX, Y: homeY}
	item.AttackCooldown = time.Duration(cooldownMS) * time.Millisecond
	if nextAttack.Valid {
		item.NextAttackAt = nextAttack.Time
	}
	return item, nil
}

func nullTime(value time.Time) any {
	if value.IsZero() {
		return nil
	}
	return value
}
