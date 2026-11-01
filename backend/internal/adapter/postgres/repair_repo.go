package postgres

import (
	"context"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
)

func scanRepair(row socialScanner) (a building.RepairJob, err error) {
	err = socialError(row.Scan(&a.ID, &a.BuildingID, &a.PlayerID, &a.BuildingType, &a.Level, &a.Workers, &a.DueAt, &a.Status))
	return
}

const repairColumns = `id,building_id,player_id,building_type,level,workers,due_at,status`

func (r *BuildingRepo) CreateRepair(ctx context.Context, a building.RepairJob) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `INSERT INTO repair_jobs(`+repairColumns+`)VALUES($1,$2,$3,$4,$5,$6,$7,$8)`, a.ID, a.BuildingID, a.PlayerID, a.BuildingType, a.Level, a.Workers, a.DueAt, a.Status)
	return err
}
func (r *BuildingRepo) PendingRepair(ctx context.Context, id building.ID) (building.RepairJob, error) {
	return scanRepair(execer(ctx, r.db).QueryRowContext(ctx, `SELECT `+repairColumns+` FROM repair_jobs WHERE building_id=$1 AND status='pending'`, id))
}
func (r *BuildingRepo) DueRepairs(ctx context.Context, now time.Time, limit int) ([]building.RepairJob, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT `+repairColumns+` FROM repair_jobs WHERE status='pending' AND due_at<=$1 ORDER BY due_at,id LIMIT $2`, now, limit)
	return collectSocial(rows, err, scanRepair)
}
func (r *BuildingRepo) LockRepair(ctx context.Context, id string) (building.RepairJob, error) {
	return scanRepair(execer(ctx, r.db).QueryRowContext(ctx, `SELECT `+repairColumns+` FROM repair_jobs WHERE id=$1 FOR UPDATE`, id))
}
func (r *BuildingRepo) FinishRepair(ctx context.Context, id, status string) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `UPDATE repair_jobs SET status=$2 WHERE id=$1 AND status='pending'`, id, status)
	return err
}

func (r *BuildingRepo) RepairWorkers(ctx context.Context, p player.ID) (n int, err error) {
	err = execer(ctx, r.db).QueryRowContext(ctx, `SELECT COALESCE(sum(workers),0) FROM repair_jobs WHERE player_id=$1 AND status='pending'`, p).Scan(&n)
	return
}
