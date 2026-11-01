package postgres

import (
	"context"
	"real-city/backend/internal/domain/player"
	"time"
)

func (r *PlayerRepo) PvPProtection(ctx context.Context, id player.ID, now time.Time, damage, health int) (state player.PvPState, allowed int, err error) {
	err = NewUnitOfWork(r.db).Do(ctx, func(ctx context.Context) error {
		q := execer(ctx, r.db)
		if _, err := q.ExecContext(ctx, `INSERT INTO player_pvp_losses(player_id,day,damage,destructions) VALUES($1,$2,0,0) ON CONFLICT DO NOTHING`, id, now.UTC().Truncate(24*time.Hour)); err != nil {
			return err
		}
		if err := q.QueryRowContext(ctx, `SELECT day,damage,destructions FROM player_pvp_losses WHERE player_id=$1 FOR UPDATE`, id).Scan(&state.Day, &state.Damage, &state.Destructions); err != nil {
			return err
		}
		var seen time.Time
		if err := q.QueryRowContext(ctx, `SELECT COALESCE(pr.updated_at,p.created_at) FROM players p LEFT JOIN player_presence pr ON pr.player_id=p.id WHERE p.id=$1`, id).Scan(&seen); err != nil {
			return err
		}
		state, allowed = player.ApplyPvPDamage(state, seen, now, damage, health)
		_, err := q.ExecContext(ctx, `UPDATE player_pvp_losses SET day=$2,damage=$3,destructions=$4 WHERE player_id=$1`, id, state.Day, state.Damage, state.Destructions)
		return err
	})
	return
}
