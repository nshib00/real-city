package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type EconomyRepo struct {
	mu           sync.RWMutex
	inventories  map[player.ID]economy.Inventory
	transactions map[player.ID][]economy.Transaction
	nodes        map[economy.NodeID]economy.ResourceNode
	jobs         map[economy.ProductionJobID]economy.ProductionJob
}

func NewEconomyRepo() *EconomyRepo {
	now := time.Now().UTC()
	nodes := map[economy.NodeID]economy.ResourceNode{
		"node_wood_1":  {ID: "node_wood_1", MapID: "dev-world", Type: "forest_cache", Resource: economy.ResourceWood, Amount: 80, MaxAmount: 80, Tile: world.Coord{X: 7, Y: 9}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_stone_1": {ID: "node_stone_1", MapID: "dev-world", Type: "stone_vein", Resource: economy.ResourceStone, Amount: 55, MaxAmount: 55, Tile: world.Coord{X: 14, Y: 5}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_1":   {ID: "node_oil_1", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 36, MaxAmount: 36, Tile: world.Coord{X: 24, Y: 18}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_2":   {ID: "node_oil_2", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 28, MaxAmount: 28, Tile: world.Coord{X: 91, Y: 73}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_3":   {ID: "node_oil_3", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 32, MaxAmount: 32, Tile: world.Coord{X: 126, Y: 35}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_4":   {ID: "node_oil_4", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 30, MaxAmount: 30, Tile: world.Coord{X: 38, Y: 124}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_5":   {ID: "node_oil_5", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 34, MaxAmount: 34, Tile: world.Coord{X: 142, Y: 116}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_oil_6":   {ID: "node_oil_6", MapID: "dev-world", Type: "oil_well", Resource: economy.ResourceOil, Amount: 26, MaxAmount: 26, Tile: world.Coord{X: 76, Y: 139}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
	}
	return &EconomyRepo{
		inventories:  make(map[player.ID]economy.Inventory),
		transactions: make(map[player.ID][]economy.Transaction),
		nodes:        nodes,
		jobs:         make(map[economy.ProductionJobID]economy.ProductionJob),
	}
}

func (r *EconomyRepo) GetInventory(ctx context.Context, playerID player.ID, coinCapacity int) (economy.Inventory, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	inventory, ok := r.inventories[playerID]
	if !ok {
		inventory = economy.NewInventory(string(playerID), time.Now().UTC(), coinCapacity)
	}
	for _, resource := range economy.AllResourceTypes() {
		if _, ok := inventory.Items[resource]; !ok {
			inventory.Items[resource] = 0
		}
	}
	inventory.CoinCapacity = coinCapacity
	r.inventories[playerID] = inventory
	return cloneInventory(inventory), nil
}

func (r *EconomyRepo) SaveInventory(ctx context.Context, inventory economy.Inventory) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.inventories[player.ID(inventory.PlayerID)] = cloneInventory(inventory)
	return nil
}

func (r *EconomyRepo) SpendResourceIfAvailable(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int, now time.Time) (bool, error) {
	_ = ctx
	if amount <= 0 {
		return false, nil
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	inventory, ok := r.inventories[playerID]
	if !ok || inventory.Items[resource] < amount {
		return false, nil
	}
	inventory.Items[resource] -= amount
	inventory.UpdatedAt = now
	r.inventories[playerID] = inventory
	return true, nil
}

func (r *EconomyRepo) AddTransaction(ctx context.Context, tx economy.Transaction) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	id := player.ID(tx.PlayerID)
	r.transactions[id] = append(r.transactions[id], tx)
	return nil
}

func (r *EconomyRepo) HasPopulationTransactions(ctx context.Context, playerID player.ID) (bool, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, transaction := range r.transactions[playerID] {
		if transaction.Resource == economy.ResourcePopulation {
			return true, nil
		}
	}
	return false, nil
}

func (r *EconomyRepo) ListTransactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := append([]economy.Transaction(nil), r.transactions[playerID]...)
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *EconomyRepo) ListResourceNodes(ctx context.Context, mapID string) ([]economy.ResourceNode, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]economy.ResourceNode, 0, len(r.nodes))
	for _, node := range r.nodes {
		if node.MapID == mapID {
			items = append(items, node)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	return items, nil
}

func (r *EconomyRepo) SaveResourceNode(ctx context.Context, node economy.ResourceNode) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.nodes[node.ID] = node
	return nil
}

func (r *EconomyRepo) FindResourceNode(ctx context.Context, id economy.NodeID) (economy.ResourceNode, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	node, ok := r.nodes[id]
	if !ok {
		return economy.ResourceNode{}, apperror.New(apperror.NotFound, "resource node not found")
	}
	return node, nil
}

func (r *EconomyRepo) ListProductionJobs(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]economy.ProductionJob, 0)
	for _, job := range r.jobs {
		if job.PlayerID == string(playerID) {
			items = append(items, job)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	return items, nil
}

func (r *EconomyRepo) ListDueProductionJobs(ctx context.Context, now time.Time, limit int) ([]economy.ProductionJob, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]economy.ProductionJob, 0)
	for _, job := range r.jobs {
		if job.State == economy.ProductionRunning && !job.CompletesAt.After(now) {
			items = append(items, job)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CompletesAt.Before(items[j].CompletesAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *EconomyRepo) SaveProductionJob(ctx context.Context, job economy.ProductionJob) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.jobs[job.ID] = job
	return nil
}

func (r *EconomyRepo) FindProductionJob(ctx context.Context, id economy.ProductionJobID) (economy.ProductionJob, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	job, ok := r.jobs[id]
	if !ok {
		return economy.ProductionJob{}, apperror.New(apperror.NotFound, "production job not found")
	}
	return job, nil
}

func cloneInventory(inventory economy.Inventory) economy.Inventory {
	items := make(map[economy.ResourceType]int, len(inventory.Items))
	for resource, amount := range inventory.Items {
		items[resource] = amount
	}
	inventory.Items = items
	return inventory
}
