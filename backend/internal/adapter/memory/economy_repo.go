package memory

import (
	"context"
	"fmt"
	"maps"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
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
		"node_wood_1":  {ID: "node_wood_1", MapID: devWorldMapID, Type: "forest_cache", Resource: economy.ResourceWood, Amount: 80, MaxAmount: 80, Tile: world.Coord{X: 7, Y: 9}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
		"node_stone_1": {ID: "node_stone_1", MapID: devWorldMapID, Type: "stone_vein", Resource: economy.ResourceStone, Amount: 55, MaxAmount: 55, Tile: world.Coord{X: 14, Y: 5}, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now},
	}
	generator := worldgen.New(devWorldMapID, devWorldSeed, devWorldSpawnRadius)
	for index, coord := range generator.OilWellTiles() {
		id := economy.NodeID(fmt.Sprintf("node_oil_%d", index+1))
		nodes[id] = economy.ResourceNode{ID: id, MapID: devWorldMapID, Type: "oil_well", Resource: economy.ResourceOil, Amount: 100000, MaxAmount: 100000, Tile: coord, State: economy.NodeNeutral, CreatedAt: now, UpdatedAt: now}
	}
	return &EconomyRepo{
		inventories:  make(map[player.ID]economy.Inventory),
		transactions: make(map[player.ID][]economy.Transaction),
		nodes:        nodes,
		jobs:         make(map[economy.ProductionJobID]economy.ProductionJob),
	}
}

func (r *EconomyRepo) GetInventory(ctx context.Context, playerID player.ID, coinCapacity int) (economy.Inventory, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.inventories[player.ID(inventory.PlayerID)] = cloneInventory(inventory)
	return nil
}

func (r *EconomyRepo) SpendResourceIfAvailable(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int, now time.Time) (bool, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	id := player.ID(tx.PlayerID)
	r.transactions[id] = append(r.transactions[id], tx)
	return nil
}

func (r *EconomyRepo) HasPopulationTransactions(ctx context.Context, playerID player.ID) (bool, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.nodes[node.ID] = node
	return nil
}

func (r *EconomyRepo) FindResourceNode(ctx context.Context, id economy.NodeID) (economy.ResourceNode, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.jobs[job.ID] = job
	return nil
}

func (r *EconomyRepo) FindProductionJob(ctx context.Context, id economy.ProductionJobID) (economy.ProductionJob, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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

func (r *EconomyRepo) Snapshot() func() {
	r.mu.RLock()
	inventories := maps.Clone(r.inventories)
	for id, v := range inventories {
		inventories[id] = cloneInventory(v)
	}
	transactions := maps.Clone(r.transactions)
	for id, v := range transactions {
		transactions[id] = append([]economy.Transaction(nil), v...)
	}
	nodes := maps.Clone(r.nodes)
	jobs := maps.Clone(r.jobs)
	r.mu.RUnlock()
	return func() {
		r.mu.Lock()
		defer r.mu.Unlock()
		r.inventories = inventories
		r.transactions = transactions
		r.nodes = nodes
		r.jobs = jobs
	}
}
