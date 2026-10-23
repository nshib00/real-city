package postgres

import (
	"context"
	"time"

	"real-city/backend/internal/domain/player"
)

func (r *PlayerRepo) SavePresence(ctx context.Context, id player.ID, x, y int, now time.Time) error {
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO player_presence (player_id, tile_x, tile_y, updated_at)
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (player_id) DO UPDATE SET tile_x = EXCLUDED.tile_x, tile_y = EXCLUDED.tile_y, updated_at = EXCLUDED.updated_at
	`, id, x, y, now)
	return err
}

func (r *PlayerRepo) ListNearbyPresence(ctx context.Context, viewer player.ID, x, y, radius int, since time.Time) ([]player.Presence, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT presence.player_id, players.name, profiles.level, presence.tile_x, presence.tile_y, presence.updated_at
		FROM player_presence AS presence
		JOIN players ON players.id = presence.player_id
		JOIN player_profiles AS profiles ON profiles.player_id = presence.player_id
		WHERE presence.updated_at >= $1 AND presence.player_id <> $2 AND players.status = 'active'
			AND LEAST(ABS(presence.tile_x - $3), 160 - ABS(presence.tile_x - $3)) <= $5
			AND LEAST(ABS(presence.tile_y - $4), 160 - ABS(presence.tile_y - $4)) <= $5
	`, since, viewer, x, y, radius)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]player.Presence, 0)
	for rows.Next() {
		var item player.Presence
		if err := rows.Scan(&item.PlayerID, &item.Name, &item.Level, &item.TileX, &item.TileY, &item.UpdatedAt); err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}
