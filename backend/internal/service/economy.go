package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

const (
	BaseCoinCapacity          = 2000
	townHallStarterPopulation = 3
)

var coinStorageCapacityByLevel = []int{
	2000,
	5000,
	10000,
	25000,
	60000,
	150000,
	350000,
	800000,
	1800000,
	4000000,
	9000000,
	20000000,
}

type skipCatchUpKey struct{}
type skipStarterPopulationKey struct{}

type EconomyService struct {
	repo      EconomyRepository
	players   PlayerRepository
	buildings BuildingRepository
	log       *slog.Logger
	now       func() time.Time
	catchUp   func(context.Context, player.ID) error
	events    *EventBus
}

func NewEconomyService(repo EconomyRepository, buildings BuildingRepository, log *slog.Logger) *EconomyService {
	return &EconomyService{repo: repo, buildings: buildings, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *EconomyService) SetPlayers(players PlayerRepository) {
	s.players = players
}

func (s *EconomyService) SetCatchUp(fn func(context.Context, player.ID) error) {
	s.catchUp = fn
}

func (s *EconomyService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *EconomyService) Inventory(ctx context.Context, playerID player.ID) (economy.Inventory, error) {
	if s.catchUp != nil && ctx.Value(skipCatchUpKey{}) != true {
		if err := s.catchUp(ctx, playerID); err != nil {
			return economy.Inventory{}, err
		}
	}
	if ctx.Value(skipCatchUpKey{}) != true {
		if err := s.ReleaseReadyFieldWorkers(ctx, playerID); err != nil {
			return economy.Inventory{}, err
		}
	}
	capacity, err := s.CoinCapacity(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	inventory, err := s.repo.GetInventory(ctx, playerID, capacity)
	if err != nil {
		return economy.Inventory{}, err
	}
	if err := s.applyInventoryPolicy(ctx, playerID, &inventory); err != nil {
		return economy.Inventory{}, err
	}
	if ctx.Value(skipStarterPopulationKey{}) == true {
		return inventory, nil
	}
	return s.ensureTownHallStarterPopulation(ctx, playerID, inventory)
}

func (s *EconomyService) ReleaseReadyFieldWorkers(ctx context.Context, playerID player.ID) error {
	if s.buildings == nil || s.repo == nil {
		return nil
	}
	now := s.now()
	items, err := s.buildings.ListByPlayer(ctx, playerID)
	if err != nil {
		return err
	}
	released := 0
	for _, item := range items {
		if item.State != building.StateActive ||
			!economy.IsFieldCropBuildingType(string(item.Type)) ||
			item.FieldStage <= 0 ||
			item.FieldStageStartedAt == nil ||
			item.FieldStageReadyAt == nil ||
			item.FieldStageReadyAt.After(now) {
			continue
		}
		amount := buildingPopulation(item)
		if amount <= 0 {
			continue
		}
		item.FieldStageStartedAt = nil
		item.UpdatedAt = now
		if err := s.buildings.Update(ctx, item); err != nil {
			return err
		}
		released += amount
		_ = s.logTransaction(ctx, playerID, economy.TransactionAdd, economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: amount}, "field:"+string(item.Type)+":workers:stage_complete")
	}
	if released <= 0 {
		return nil
	}
	capacity, err := s.CoinCapacity(ctx, playerID)
	if err != nil {
		return err
	}
	inventory, err := s.repo.GetInventory(ctx, playerID, capacity)
	if err != nil {
		return err
	}
	if err := s.applyInventoryPolicy(ctx, playerID, &inventory); err != nil {
		return err
	}
	inventory.Add([]economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: released}}, now)
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return err
	}
	if s.events != nil {
		s.events.Publish(Event{Type: EventInventoryChanged, PlayerID: playerID, Payload: InventoryPayload{Inventory: inventory}})
	}
	return nil
}

func WithoutCatchUp(ctx context.Context) context.Context {
	return context.WithValue(ctx, skipCatchUpKey{}, true)
}

func withoutStarterPopulationBackfill(ctx context.Context) context.Context {
	return context.WithValue(ctx, skipStarterPopulationKey{}, true)
}

func (s *EconomyService) Spend(ctx context.Context, playerID player.ID, cost []economy.ResourceAmount, reason string) (economy.Inventory, error) {
	inventory, err := s.Inventory(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	if !inventory.Spend(cost, s.now()) {
		fields := make(map[string]string)
		for _, item := range cost {
			available := inventory.Items[item.Resource]
			if available < item.Amount {
				fields[string(item.Resource)] = fmt.Sprintf("need %d, have %d", item.Amount, available)
			}
		}
		s.log.Warn("economy.resource.shortage", "event", "economy.resource.shortage", "player_id", playerID, "reason", reason, "missing", fields)
		return economy.Inventory{}, apperror.WithFields(apperror.Conflict, "not enough resources", fields)
	}
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return economy.Inventory{}, err
	}
	for _, item := range cost {
		_ = s.logTransaction(ctx, playerID, economy.TransactionSpend, item, reason)
	}
	if s.events != nil {
		s.events.Publish(Event{Type: EventInventoryChanged, PlayerID: playerID, Payload: InventoryPayload{Inventory: inventory}})
	}
	return inventory, nil
}

func (s *EconomyService) Add(ctx context.Context, playerID player.ID, items []economy.ResourceAmount, reason string) (economy.Inventory, []economy.ResourceAmount, error) {
	inventory, err := s.Inventory(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, nil, err
	}
	overflow := inventory.Add(items, s.now())
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return economy.Inventory{}, nil, err
	}
	for _, item := range items {
		_ = s.logTransaction(ctx, playerID, economy.TransactionAdd, item, reason)
	}
	for _, item := range overflow {
		s.log.Warn("economy.coin_capacity.overflow", "event", "economy.coin_capacity.overflow", "player_id", playerID, "overflow", item.Amount)
	}
	if s.events != nil {
		s.events.Publish(Event{Type: EventInventoryChanged, PlayerID: playerID, Payload: InventoryPayload{Inventory: inventory}})
	}
	return inventory, overflow, nil
}

func (s *EconomyService) Transactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error) {
	return s.repo.ListTransactions(ctx, playerID, limit)
}

func (s *EconomyService) CoinCapacity(ctx context.Context, playerID player.ID) (int, error) {
	if s.buildings == nil {
		return BaseCoinCapacity, nil
	}
	buildings, err := s.buildings.ListByPlayer(ctx, playerID)
	if err != nil {
		return 0, err
	}
	capacity := BaseCoinCapacity
	for _, item := range buildings {
		if item.Type == building.TypeCoinStorage && coinStorageGivesCapacity(item) {
			capacity += coinStorageCapacity(item.Level)
		}
	}
	return capacity, nil
}

func (s *EconomyService) applyInventoryPolicy(ctx context.Context, playerID player.ID, inventory *economy.Inventory) error {
	if s.players == nil {
		return nil
	}
	item, err := s.players.FindByID(ctx, playerID)
	if err != nil {
		return err
	}
	inventory.BypassCoinCapacity = item.Role == player.RoleAdmin
	return nil
}

func coinStorageGivesCapacity(item building.Building) bool {
	return item.State == building.StateActive || item.State == building.StateDamaged
}

func coinStorageCapacity(level int) int {
	if level < 1 {
		level = 1
	}
	if level > len(coinStorageCapacityByLevel) {
		level = len(coinStorageCapacityByLevel)
	}
	return coinStorageCapacityByLevel[level-1]
}

func (s *EconomyService) ensureTownHallStarterPopulation(ctx context.Context, playerID player.ID, inventory economy.Inventory) (economy.Inventory, error) {
	if s.buildings == nil || inventory.Items[economy.ResourcePopulation] >= townHallStarterPopulation {
		return inventory, nil
	}
	items, err := s.buildings.ListByPlayer(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	hasActiveTownHall := false
	hasActiveConstruction := false
	for _, item := range items {
		if item.Type == building.TypeTownHall && (item.State == building.StateActive || item.State == building.StateDamaged) {
			hasActiveTownHall = true
		}
		if item.State == building.StateBuilding || item.State == building.StatePlanned {
			hasActiveConstruction = true
		}
	}
	if !hasActiveTownHall || hasActiveConstruction {
		return inventory, nil
	}
	inventory.Items[economy.ResourcePopulation] = townHallStarterPopulation
	inventory.UpdatedAt = s.now()
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return economy.Inventory{}, err
	}
	return inventory, nil
}

func (s *EconomyService) logTransaction(ctx context.Context, playerID player.ID, kind economy.TransactionKind, item economy.ResourceAmount, reason string) error {
	tx := economy.Transaction{
		ID:        economy.TransactionID(fmt.Sprintf("tx_%d_%s", s.now().UnixNano(), item.Resource)),
		PlayerID:  string(playerID),
		Kind:      kind,
		Resource:  item.Resource,
		Amount:    item.Amount,
		Reason:    reason,
		CreatedAt: s.now(),
	}
	s.log.Info("economy.resource.changed", "event", "economy.resource.changed", "player_id", playerID, "kind", kind, "resource", item.Resource, "amount", item.Amount, "reason", reason)
	return s.repo.AddTransaction(ctx, tx)
}
