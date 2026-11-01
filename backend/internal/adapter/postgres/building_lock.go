package postgres

import (
	"context"
	"database/sql"
	"errors"
	"real-city/backend/internal/domain/building"
	"real-city/backend/pkg/apperror"
)

// Must run inside a UnitOfWork; serializes production with damage/deletion.
func (r *BuildingRepo) LockForAction(ctx context.Context, id building.ID) error {
	var found string
	err := execer(ctx, r.db).QueryRowContext(ctx, `SELECT id FROM buildings WHERE id=$1 FOR UPDATE`, id).Scan(&found)
	if errors.Is(err, sql.ErrNoRows) {
		return apperror.New(apperror.NotFound, "Постройка не найдена")
	}
	return err
}

func (r *BuildingRepo) LockPlacement(ctx context.Context) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `SELECT pg_advisory_xact_lock(721032)`)
	return err
}
