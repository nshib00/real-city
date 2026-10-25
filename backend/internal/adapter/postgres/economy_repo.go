package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/lib/pq"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type EconomyRepo struct {
	db *sql.DB
}

func NewEconomyRepo(db *sql.DB) *EconomyRepo {
	return &EconomyRepo{db: db}
}

func (r *EconomyRepo) GetInventory(ctx context.Context, playerID player.ID, coinCapacity int) (economy.Inventory, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT resource, amount, updated_at FROM player_inventories WHERE player_id = $1`, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	defer rows.Close()
	inventory := economy.EmptyInventory(string(playerID), time.Now().UTC(), coinCapacity)
	rowCount := 0
	for rows.Next() {
		var resource string
		var amount int64
		var updatedAt time.Time
		if err := rows.Scan(&resource, &amount, &updatedAt); err != nil {
			return economy.Inventory{}, err
		}
		inventory.Items[economy.ResourceType(resource)] = int(amount)
		if rowCount == 0 || updatedAt.After(inventory.UpdatedAt) {
			inventory.UpdatedAt = updatedAt
		}
		rowCount++
	}
	if err := rows.Err(); err != nil {
		return economy.Inventory{}, err
	}
	if rowCount == 0 {
		inventory = economy.NewInventory(string(playerID), time.Now().UTC(), coinCapacity)
		if err := r.SaveInventory(ctx, inventory); err != nil {
			return economy.Inventory{}, err
		}
		return inventory, nil
	}
	for _, resource := range economy.AllResourceTypes() {
		if _, ok := inventory.Items[resource]; !ok {
			inventory.Items[resource] = 0
		}
	}
	return inventory, nil
}

func (r *EconomyRepo) SaveInventory(ctx context.Context, inventory economy.Inventory) error {
	if len(inventory.Items) == 0 {
		return nil
	}
	resources := make([]string, 0, len(inventory.Items))
	amounts := make([]int64, 0, len(inventory.Items))
	for resource, amount := range inventory.Items {
		resources = append(resources, string(resource))
		amounts = append(amounts, int64(amount))
	}
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO player_inventories (player_id, resource, amount, updated_at)
		SELECT $1, entries.resource, entries.amount, $4
		FROM unnest($2::text[], $3::bigint[]) AS entries(resource, amount)
		ON CONFLICT (player_id, resource)
		DO UPDATE SET amount = EXCLUDED.amount, updated_at = EXCLUDED.updated_at
	`, inventory.PlayerID, pq.Array(resources), pq.Array(amounts), inventory.UpdatedAt)
	return err
}

func (r *EconomyRepo) SpendResourceIfAvailable(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int, now time.Time) (bool, error) {
	if amount <= 0 {
		return false, nil
	}
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		UPDATE player_inventories SET amount = amount - $3, updated_at = $4
		WHERE player_id = $1 AND resource = $2 AND amount >= $3
	`, playerID, resource, amount, now)
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
}

func (r *EconomyRepo) AddTransaction(ctx context.Context, tx economy.Transaction) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO economy_transactions (id, player_id, kind, resource, amount, reason, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, tx.ID, tx.PlayerID, tx.Kind, tx.Resource, tx.Amount, tx.Reason, tx.CreatedAt)
	return err
}

func (r *EconomyRepo) HasPopulationTransactions(ctx context.Context, playerID player.ID) (bool, error) {
	var exists bool
	err := execer(ctx, r.db).QueryRowContext(ctx, `SELECT EXISTS (SELECT 1 FROM economy_transactions WHERE player_id = $1 AND resource = $2)`, playerID, economy.ResourcePopulation).Scan(&exists)
	return exists, err
}

func (r *EconomyRepo) ListTransactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error) {
	if limit <= 0 {
		limit = 20
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, player_id, kind, resource, amount, reason, created_at
		FROM economy_transactions
		WHERE player_id = $1
		ORDER BY created_at DESC
		LIMIT $2
	`, playerID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]economy.Transaction, 0)
	for rows.Next() {
		var item economy.Transaction
		if err := rows.Scan(&item.ID, &item.PlayerID, &item.Kind, &item.Resource, &item.Amount, &item.Reason, &item.CreatedAt); err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *EconomyRepo) ListResourceNodes(ctx context.Context, mapID string) ([]economy.ResourceNode, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, map_id, type, resource, amount, max_amount, state, COALESCE(owner_id, ''), tile_x, tile_y, respawn_at, created_at, updated_at
		FROM resource_nodes
		WHERE map_id = $1
		ORDER BY id
	`, mapID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]economy.ResourceNode, 0)
	for rows.Next() {
		node, err := scanResourceNode(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, node)
	}
	return items, rows.Err()
}

func (r *EconomyRepo) SaveResourceNode(ctx context.Context, node economy.ResourceNode) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO resource_nodes (id, map_id, type, resource, amount, max_amount, state, owner_id, tile_x, tile_y, respawn_at, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, NULLIF($8, ''), $9, $10, $11, $12, $13)
		ON CONFLICT (id)
		DO UPDATE SET amount = EXCLUDED.amount, state = EXCLUDED.state, owner_id = EXCLUDED.owner_id, tile_x = EXCLUDED.tile_x, tile_y = EXCLUDED.tile_y, respawn_at = EXCLUDED.respawn_at, updated_at = EXCLUDED.updated_at
	`, node.ID, node.MapID, node.Type, node.Resource, node.Amount, node.MaxAmount, node.State, node.OwnerID, node.Tile.X, node.Tile.Y, node.RespawnAt, node.CreatedAt, node.UpdatedAt)
	return err
}

func (r *EconomyRepo) FindResourceNode(ctx context.Context, id economy.NodeID) (economy.ResourceNode, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT id, map_id, type, resource, amount, max_amount, state, COALESCE(owner_id, ''), tile_x, tile_y, respawn_at, created_at, updated_at
		FROM resource_nodes
		WHERE id = $1
	`, id)
	node, err := scanResourceNode(row)
	if errors.Is(err, sql.ErrNoRows) {
		return economy.ResourceNode{}, apperror.New(apperror.NotFound, "resource node not found")
	}
	return node, err
}

func (r *EconomyRepo) ListProductionJobs(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at
		FROM production_jobs
		WHERE player_id = $1
		ORDER BY created_at DESC
	`, playerID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]economy.ProductionJob, 0)
	for rows.Next() {
		job, err := scanProductionJob(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, job)
	}
	return items, rows.Err()
}

func (r *EconomyRepo) ListDueProductionJobs(ctx context.Context, now time.Time, limit int) ([]economy.ProductionJob, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at
		FROM production_jobs
		WHERE state = $1 AND completes_at <= $2
		ORDER BY completes_at, id
		LIMIT $3
	`, economy.ProductionRunning, now, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]economy.ProductionJob, 0)
	for rows.Next() {
		job, err := scanProductionJob(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, job)
	}
	return items, rows.Err()
}

func (r *EconomyRepo) SaveProductionJob(ctx context.Context, job economy.ProductionJob) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO production_jobs (id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		ON CONFLICT (id)
		DO UPDATE SET state = EXCLUDED.state, updated_at = EXCLUDED.updated_at
	`, job.ID, job.PlayerID, job.BuildingID, job.RecipeID, job.State, job.StartedAt, job.CompletesAt, job.CreatedAt, job.UpdatedAt)
	return err
}

func (r *EconomyRepo) FindProductionJob(ctx context.Context, id economy.ProductionJobID) (economy.ProductionJob, error) {
	row := execer(ctx, r.db).QueryRowContext(ctx, `
		SELECT id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at
		FROM production_jobs
		WHERE id = $1
	`, id)
	job, err := scanProductionJob(row)
	if errors.Is(err, sql.ErrNoRows) {
		return economy.ProductionJob{}, apperror.New(apperror.NotFound, "production job not found")
	}
	return job, err
}

type economyScanner interface {
	Scan(dest ...any) error
}

func scanResourceNode(row economyScanner) (economy.ResourceNode, error) {
	var node economy.ResourceNode
	var tileX, tileY int
	if err := row.Scan(&node.ID, &node.MapID, &node.Type, &node.Resource, &node.Amount, &node.MaxAmount, &node.State, &node.OwnerID, &tileX, &tileY, &node.RespawnAt, &node.CreatedAt, &node.UpdatedAt); err != nil {
		return economy.ResourceNode{}, err
	}
	node.Tile = world.Coord{X: tileX, Y: tileY}
	return node, nil
}

func scanProductionJob(row economyScanner) (economy.ProductionJob, error) {
	var job economy.ProductionJob
	if err := row.Scan(&job.ID, &job.PlayerID, &job.BuildingID, &job.RecipeID, &job.State, &job.StartedAt, &job.CompletesAt, &job.CreatedAt, &job.UpdatedAt); err != nil {
		return economy.ProductionJob{}, err
	}
	return job, nil
}
