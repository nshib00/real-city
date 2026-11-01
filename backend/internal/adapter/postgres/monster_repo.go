package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
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

func (r *MonsterRepo) ListActiveForTick(ctx context.Context, mapID string, now time.Time, limit int) (items []monster.Monster, resultErr error) {
	defer observe("monster.list_active_for_tick", time.Now(), &resultErr)
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, monsterSelect()+`
		WHERE map_id = $1 AND state <> 'dead' AND next_ai_at <= $2
		ORDER BY next_ai_at, id
		LIMIT $3
	`, mapID, now, limit)
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

func (r *MonsterRepo) UpdateIfCurrent(ctx context.Context, previous, next monster.Monster) (bool, error) {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE monsters
		SET state = $2, tile_x = $3, tile_y = $4, target_id = $5, target_type = $6,
			health = $7, next_attack_at = $8, last_moved_at = $9, updated_at = $10, shock_until = $17, next_ai_at = $18
		WHERE id = $1 AND state = $11 AND state <> $12 AND health = $13
			AND tile_x = $14 AND tile_y = $15 AND updated_at = $16
	`, next.ID, next.State, next.Tile.X, next.Tile.Y, next.TargetID, next.TargetType,
		next.Health, nullTime(next.NextAttackAt), next.LastMovedAt, next.UpdatedAt,
		previous.State, monster.StateDead, previous.Health, previous.Tile.X, previous.Tile.Y, previous.UpdatedAt, nullTime(next.ShockUntil), nextMonsterAIAt(next))
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
}

func nextMonsterAIAt(next monster.Monster) time.Time {
	if next.State == monster.StateWandering && next.TargetID == "" {
		return next.UpdatedAt.Add(2 * time.Second)
	}
	return next.UpdatedAt.Add(time.Second)
}

func (r *MonsterRepo) WakeNearBuilding(ctx context.Context, mapID string, tile world.Coord, footprint building.Footprint, now time.Time) error {
	extent := max(1, footprint.Width, footprint.Height) - 1
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE monsters SET next_ai_at = $4
		WHERE map_id = $1 AND state = 'wandering' AND next_ai_at > $4
		  AND LEAST(ABS(tile_x - $2), $5 - ABS(tile_x - $2)) <= aggro_radius + $6
		  AND LEAST(ABS(tile_y - $3), $5 - ABS(tile_y - $3)) <= aggro_radius + $6
	`, mapID, tile.X, tile.Y, now, world.WorldSize, extent)
	return err
}

func (r *MonsterRepo) CountAliveBySpawn(ctx context.Context, mapID string) (result map[monster.SpawnID]int, resultErr error) {
	defer observe("monster.count_alive_by_spawn", time.Now(), &resultErr)
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT spawn_id, COUNT(*)
		FROM monsters
		WHERE map_id = $1 AND state <> 'dead' AND spawn_id <> ''
		GROUP BY spawn_id
	`, mapID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	counts := make(map[monster.SpawnID]int)
	for rows.Next() {
		var spawnID monster.SpawnID
		var count int
		if err := rows.Scan(&spawnID, &count); err != nil {
			return nil, err
		}
		counts[spawnID] = count
	}
	return counts, rows.Err()
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
		ON CONFLICT (id) DO UPDATE SET type = EXCLUDED.type, tile_x = EXCLUDED.tile_x, tile_y = EXCLUDED.tile_y, radius = EXCLUDED.radius, max_alive = EXCLUDED.max_alive, cooldown_ms = EXCLUDED.cooldown_ms, next_spawn_at = EXCLUDED.next_spawn_at, updated_at = EXCLUDED.updated_at
	`, item.ID, item.MapID, item.Type, item.Tile.X, item.Tile.Y, item.Radius, item.MaxAlive, int(item.Cooldown/time.Millisecond), item.NextSpawnAt, item.CreatedAt, item.UpdatedAt)
	return err
}

func (r *MonsterRepo) CreateLootDrop(ctx context.Context, item monster.LootDrop) error {
	raw, err := json.Marshal(item.Items)
	if err != nil {
		return err
	}
	_, err = execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO monster_loot_drops (id, map_id, monster_id, tile_x, tile_y, items, claimed_by, claimed_at, created_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
	`, item.ID, item.MapID, item.MonsterID, item.Tile.X, item.Tile.Y, raw, item.ClaimedBy, item.ClaimedAt, item.CreatedAt)
	return err
}

func (r *MonsterRepo) FindLootDrop(ctx context.Context, id monster.LootDropID) (monster.LootDrop, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT id, map_id, monster_id, tile_x, tile_y, items, claimed_by, claimed_at, created_at
		FROM monster_loot_drops
		WHERE id = $1
	`, id)
	item, err := scanLootDrop(row)
	if errors.Is(err, sql.ErrNoRows) {
		return monster.LootDrop{}, apperror.New(apperror.NotFound, "loot drop not found")
	}
	return item, err
}

func (r *MonsterRepo) ListLootDropsByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.LootDrop, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, monster_id, tile_x, tile_y, items, claimed_by, claimed_at, created_at
		FROM monster_loot_drops
		WHERE map_id = $1 AND claimed_by = '' AND tile_x BETWEEN $2 AND $3 AND tile_y BETWEEN $4 AND $5
		ORDER BY created_at, id
	`, mapID, minX, maxX, minY, maxY)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]monster.LootDrop, 0)
	for rows.Next() {
		item, err := scanLootDrop(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *MonsterRepo) ClaimLootDrop(ctx context.Context, id monster.LootDropID, playerID player.ID, now time.Time) (monster.LootDrop, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		UPDATE monster_loot_drops
		SET claimed_by = $2, claimed_at = $3
		WHERE id = $1 AND claimed_by = ''
		RETURNING id, map_id, monster_id, tile_x, tile_y, items, claimed_by, claimed_at, created_at
	`, id, playerID, now)
	item, err := scanLootDrop(row)
	if errors.Is(err, sql.ErrNoRows) {
		existing, findErr := r.FindLootDrop(ctx, id)
		if findErr != nil {
			return monster.LootDrop{}, findErr
		}
		if existing.ClaimedBy != "" {
			return monster.LootDrop{}, apperror.New(apperror.Conflict, "loot drop is already claimed")
		}
		return monster.LootDrop{}, apperror.New(apperror.NotFound, "loot drop not found")
	}
	return item, err
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
		INSERT INTO monsters (id, map_id, spawn_id, type, state, tile_x, tile_y, home_tile_x, home_tile_y, target_id, target_type, health, max_health, damage, speed_tiles, aggro_radius, attack_range, attack_cooldown_ms, next_attack_at, last_moved_at, loot_coins, created_at, updated_at, shock_until, creator_id, expires_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26)
		ON CONFLICT (id) DO UPDATE SET spawn_id = EXCLUDED.spawn_id, state = EXCLUDED.state, tile_x = EXCLUDED.tile_x, tile_y = EXCLUDED.tile_y, target_id = EXCLUDED.target_id, target_type = EXCLUDED.target_type, health = EXCLUDED.health, next_attack_at = EXCLUDED.next_attack_at, last_moved_at = EXCLUDED.last_moved_at, updated_at = EXCLUDED.updated_at, shock_until = EXCLUDED.shock_until, next_ai_at = now()
	`, item.ID, item.MapID, item.SpawnID, item.Type, item.State, item.Tile.X, item.Tile.Y, item.HomeTile.X, item.HomeTile.Y, item.TargetID, item.TargetType, item.Health, item.MaxHealth, item.Damage, item.SpeedTiles, item.AggroRadius, item.AttackRange, int(item.AttackCooldown/time.Millisecond), nullTime(item.NextAttackAt), item.LastMovedAt, item.LootCoins, item.CreatedAt, item.UpdatedAt, nullTime(item.ShockUntil), item.CreatorID, nullTime(item.ExpiresAt))
	return err
}

func monsterSelect() string {
	return `SELECT id, map_id, spawn_id, type, state, tile_x, tile_y, home_tile_x, home_tile_y, target_id, target_type, health, max_health, damage, speed_tiles, aggro_radius, attack_range, attack_cooldown_ms, next_attack_at, last_moved_at, loot_coins, created_at, updated_at, shock_until, creator_id, expires_at FROM monsters`
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
	var shockUntil sql.NullTime
	var expiresAt sql.NullTime
	if err := row.Scan(&item.ID, &item.MapID, &item.SpawnID, &item.Type, &item.State, &tileX, &tileY, &homeX, &homeY, &item.TargetID, &item.TargetType, &item.Health, &item.MaxHealth, &item.Damage, &item.SpeedTiles, &item.AggroRadius, &item.AttackRange, &cooldownMS, &nextAttack, &item.LastMovedAt, &item.LootCoins, &item.CreatedAt, &item.UpdatedAt, &shockUntil, &item.CreatorID, &expiresAt); err != nil {
		return monster.Monster{}, err
	}
	if expiresAt.Valid {
		item.ExpiresAt = expiresAt.Time
	}
	item.Tile = world.Coord{X: tileX, Y: tileY}
	item.HomeTile = world.Coord{X: homeX, Y: homeY}
	item.AttackCooldown = time.Duration(cooldownMS) * time.Millisecond
	if nextAttack.Valid {
		item.NextAttackAt = nextAttack.Time
	}
	if shockUntil.Valid {
		item.ShockUntil = shockUntil.Time
	}
	return item, nil
}

func scanLootDrop(row monsterScanner) (monster.LootDrop, error) {
	var item monster.LootDrop
	var tileX, tileY int
	var raw []byte
	var claimedAt sql.NullTime
	if err := row.Scan(&item.ID, &item.MapID, &item.MonsterID, &tileX, &tileY, &raw, &item.ClaimedBy, &claimedAt, &item.CreatedAt); err != nil {
		return monster.LootDrop{}, err
	}
	if len(raw) > 0 {
		if err := json.Unmarshal(raw, &item.Items); err != nil {
			return monster.LootDrop{}, err
		}
	}
	if item.Items == nil {
		item.Items = []economy.ResourceAmount{}
	}
	item.Tile = world.Coord{X: tileX, Y: tileY}
	if claimedAt.Valid {
		item.ClaimedAt = &claimedAt.Time
	}
	return item, nil
}

func nullTime(value time.Time) any {
	if value.IsZero() {
		return nil
	}
	return value
}
