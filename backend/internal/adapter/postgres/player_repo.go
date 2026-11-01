package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type PlayerRepo struct {
	db *sql.DB
}

func NewPlayerRepo(db *sql.DB) *PlayerRepo {
	return &PlayerRepo{db: db}
}

func (r *PlayerRepo) Create(ctx context.Context, p player.Player) error {
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback()
		}
	}()

	_, err = tx.ExecContext(ctx, `
		INSERT INTO players (id, email, name, password_hash, status, role, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`, p.ID, p.Email, p.Name, p.PasswordHash, p.Status, roleOrDefault(p.Role), p.CreatedAt, p.UpdatedAt)
	if err != nil {
		return mapPostgresConflict(err)
	}

	_, err = tx.ExecContext(ctx, `
		INSERT INTO player_profiles (
			player_id, display_name, avatar_url, attack_alerts, production_ready,
			market_updates, render_quality, city_name, level, xp, updated_at,avatar_id,banner_id,title,home_center_id
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,$12,$13,$14,$15)
	`, p.ID, p.Profile.DisplayName, p.Profile.AvatarURL, p.Profile.Settings.Notifications.AttackAlerts,
		p.Profile.Settings.Notifications.ProductionReady, p.Profile.Settings.Notifications.MarketUpdates,
		p.Profile.Settings.RenderQuality, p.Profile.CityName, p.Profile.Level, p.Profile.XP, p.Profile.UpdatedAt, p.Profile.AvatarID, p.Profile.BannerID, p.Profile.Title, p.Profile.HomeCenterID)
	if err != nil {
		return mapPostgresConflict(err)
	}

	return tx.Commit()
}

func (r *PlayerRepo) FindByID(ctx context.Context, id player.ID) (player.Player, error) {
	return r.findOne(ctx, "p.id = $1", string(id))
}

func (r *PlayerRepo) XPEventAmount(ctx context.Context, id player.ID, key string) (int, error) {
	var amount int
	err := execer(ctx, r.db).QueryRowContext(ctx, `SELECT amount FROM player_xp_events WHERE event_key=$1 AND player_id=$2`, key, id).Scan(&amount)
	if errors.Is(err, sql.ErrNoRows) {
		return 0, nil
	}
	return amount, err
}

func (r *PlayerRepo) FindByEmail(ctx context.Context, email string) (player.Player, error) {
	return r.findOne(ctx, "p.email = $1", player.NormalizeEmail(email))
}

func (r *PlayerRepo) UpdateProfile(ctx context.Context, id player.ID, profile player.Profile) (player.Player, error) {
	now := time.Now().UTC()
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE player_profiles
		SET display_name = $2, avatar_url = $3, attack_alerts = $4, production_ready = $5,
			market_updates = $6, render_quality = $7, city_name = $8, updated_at = $9,avatar_id=$10,banner_id=$11,title=$12,home_center_id=$13
		WHERE player_id = $1
	`, id, profile.DisplayName, profile.AvatarURL, profile.Settings.Notifications.AttackAlerts,
		profile.Settings.Notifications.ProductionReady, profile.Settings.Notifications.MarketUpdates,
		profile.Settings.RenderQuality, profile.CityName, now, profile.AvatarID, profile.BannerID, profile.Title, profile.HomeCenterID)
	if err != nil {
		return player.Player{}, err
	}
	return r.FindByID(ctx, id)
}

func (r *PlayerRepo) UpdateProgress(ctx context.Context, id player.ID, xp int, level int) (player.Player, error) {
	now := time.Now().UTC()
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE player_profiles
		SET xp = $2, level = $3, updated_at = $4
		WHERE player_id = $1
	`, id, xp, level, now)
	if err != nil {
		return player.Player{}, err
	}
	if rows, _ := result.RowsAffected(); rows == 0 {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	return r.FindByID(ctx, id)
}

func (r *PlayerRepo) AwardXPEvent(ctx context.Context, id player.ID, amount int, reason string, eventKey string) (bool, error) {
	if amount <= 0 {
		return false, nil
	}
	tx, ownsTransaction := ctx.Value(txKey{}).(*sql.Tx)
	if !ownsTransaction {
		var err error
		tx, err = r.db.BeginTx(ctx, nil)
		if err != nil {
			return false, err
		}
		defer tx.Rollback()
	}
	var currentXP int
	if err := tx.QueryRowContext(ctx, `SELECT xp FROM player_profiles WHERE player_id = $1 FOR UPDATE`, id).Scan(&currentXP); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return false, apperror.New(apperror.NotFound, "player not found")
		}
		return false, err
	}

	var count, earned, allEarned int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FILTER(WHERE reason=$2),COALESCE(sum(amount) FILTER(WHERE reason=$2),0),COALESCE(sum(amount),0) FROM player_xp_events WHERE player_id=$1 AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'`, id, reason).Scan(&count, &earned, &allEarned); err != nil {
		return false, err
	}
	applied := max(0, min(player.CappedXP(amount, reason, count, earned, allEarned), 2147483647-currentXP))
	result, err := tx.ExecContext(ctx, `INSERT INTO player_xp_events(event_key,player_id,amount,requested_amount,reason) VALUES($1,$2,$3,$4,$5) ON CONFLICT(event_key) DO NOTHING`, eventKey, id, applied, amount, reason)
	if err != nil {
		return false, err
	}
	n, err := result.RowsAffected()
	if err != nil {
		return false, err
	}
	if n == 0 {
		return false, nil
	}
	nextXP := currentXP + applied
	if _, err = tx.ExecContext(ctx, `UPDATE player_profiles SET xp=$2,level=$3,updated_at=now() WHERE player_id=$1`, id, nextXP, player.LevelForXP(nextXP)); err != nil {
		return false, err
	}
	if ownsTransaction {
		return applied > 0, nil
	}
	return applied > 0, tx.Commit()
}

func (r *PlayerRepo) UpdatePasswordHash(ctx context.Context, id player.ID, passwordHash string) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE players SET password_hash = $2, updated_at = $3 WHERE id = $1 AND status <> 'deleted'`, id, passwordHash, time.Now().UTC())
	if err != nil {
		return err
	}
	if rows, _ := result.RowsAffected(); rows == 0 {
		return apperror.New(apperror.NotFound, "player not found")
	}
	return nil
}

func (r *PlayerRepo) Delete(ctx context.Context, id player.ID) error {
	result, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE players SET status = 'deleted', updated_at = $2 WHERE id = $1 AND role <> 'admin'`, id, time.Now().UTC())
	if err != nil {
		return err
	}
	if rows, _ := result.RowsAffected(); rows == 0 {
		return apperror.New(apperror.NotFound, "player not found")
	}
	return nil
}

func (r *PlayerRepo) findOne(ctx context.Context, predicate string, arg string) (player.Player, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT
			p.id, p.email, p.name, p.password_hash, p.status, p.role, p.created_at, p.updated_at,
			pr.display_name, pr.avatar_url, pr.attack_alerts, pr.production_ready,
			pr.market_updates, pr.render_quality, pr.city_name, pr.level, pr.xp, pr.updated_at, pr.avatar_id,pr.banner_id,pr.title,pr.home_center_id
		FROM players p
		JOIN player_profiles pr ON pr.player_id = p.id
		WHERE `+predicate+` AND p.status <> 'deleted'
	`, arg)
	return scanPlayer(row)
}

type rowScanner interface {
	Scan(dest ...any) error
}

func scanPlayer(row rowScanner) (player.Player, error) {
	var p player.Player
	err := row.Scan(
		&p.ID,
		&p.Email,
		&p.Name,
		&p.PasswordHash,
		&p.Status,
		&p.Role,
		&p.CreatedAt,
		&p.UpdatedAt,
		&p.Profile.DisplayName,
		&p.Profile.AvatarURL,
		&p.Profile.Settings.Notifications.AttackAlerts,
		&p.Profile.Settings.Notifications.ProductionReady,
		&p.Profile.Settings.Notifications.MarketUpdates,
		&p.Profile.Settings.RenderQuality,
		&p.Profile.CityName,
		&p.Profile.Level,
		&p.Profile.XP,
		&p.Profile.UpdatedAt,
		&p.Profile.AvatarID, &p.Profile.BannerID, &p.Profile.Title, &p.Profile.HomeCenterID,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return player.Player{}, apperror.New(apperror.NotFound, "player not found")
	}
	p.Profile = player.NormalizeProfile(p.Profile)
	return p, err
}

func roleOrDefault(role player.Role) player.Role {
	if role == "" {
		return player.RoleUser
	}
	return role
}

func mapPostgresConflict(err error) error {
	if err == nil {
		return nil
	}
	return apperror.Wrap(apperror.Conflict, "player email or name is already taken", err)
}
