package service

import (
	"context"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

type PlayerRepository interface {
	Create(ctx context.Context, p player.Player) error
	SavePresence(ctx context.Context, id player.ID, x, y int, now time.Time) error
	ListNearbyPresence(ctx context.Context, viewer player.ID, x, y, radius int, since time.Time) ([]player.Presence, error)
	FindByID(ctx context.Context, id player.ID) (player.Player, error)
	FindByEmail(ctx context.Context, email string) (player.Player, error)
	UpdateProfile(ctx context.Context, id player.ID, profile player.Profile) (player.Player, error)
	UpdateProgress(ctx context.Context, id player.ID, xp int, level int) (player.Player, error)
	AwardXPEvent(ctx context.Context, id player.ID, amount int, reason string, eventKey string) (bool, error)
	UpdatePasswordHash(ctx context.Context, id player.ID, passwordHash string) error
	Delete(ctx context.Context, id player.ID) error
}

type SessionStore interface {
	Save(ctx context.Context, session player.Session) error
	FindByRefreshTokenHash(ctx context.Context, tokenHash string) (player.Session, error)
	Revoke(ctx context.Context, sessionID player.SessionID) error
	RevokePlayer(ctx context.Context, playerID player.ID) error
}

type WorldRepository interface {
	GetMap(ctx context.Context, id string) (world.WorldMap, error)
	GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (chunk world.Chunk, cacheHit bool, err error)
	GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error)
	GetOrCreateChunksFresh(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error)
	UpdateTile(ctx context.Context, tile world.Tile) error
}

type BuildingRepository interface {
	Create(ctx context.Context, b building.Building) error
	FindByID(ctx context.Context, id building.ID) (building.Building, error)
	ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error)
	PlayerPlacementStats(ctx context.Context, playerID player.ID) (building.PlacementStats, error)
	ListByMap(ctx context.Context, mapID string) ([]building.Building, error)
	ListByChunk(ctx context.Context, mapID string, coord world.ChunkCoord) ([]building.Building, error)
	ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error)
	ListIntersectingFootprint(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error)
	ListDue(ctx context.Context, now time.Time, limit int) ([]building.Building, error)
	ListRuinedRuins(ctx context.Context, limit int) ([]building.Building, error)
	ListReadyCannons(ctx context.Context, mapID string, now time.Time, afterID building.ID, limit int) ([]building.Building, error)
	ClaimCannonShot(ctx context.Context, id building.ID, now, next time.Time, targetID string, expectedHealth int) (bool, error)
	ConsumeTrapCharge(ctx context.Context, id building.ID, expectedHealth int) (bool, error)
	DamageIfCurrent(ctx context.Context, id building.ID, expectedHealth, damage int, now time.Time) (building.Building, bool, error)
	Update(ctx context.Context, b building.Building) error
	RelocateIfCurrent(ctx context.Context, previous, next building.Building) (bool, error)
	Delete(ctx context.Context, id building.ID) error
}

type EconomyRepository interface {
	SpendResourceIfAvailable(ctx context.Context, playerID player.ID, resource economy.ResourceType, amount int, now time.Time) (bool, error)
	GetInventory(ctx context.Context, playerID player.ID, coinCapacity int) (economy.Inventory, error)
	SaveInventory(ctx context.Context, inventory economy.Inventory) error
	AddTransaction(ctx context.Context, tx economy.Transaction) error
	HasPopulationTransactions(ctx context.Context, playerID player.ID) (bool, error)
	ListTransactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error)
	ListResourceNodes(ctx context.Context, mapID string) ([]economy.ResourceNode, error)
	SaveResourceNode(ctx context.Context, node economy.ResourceNode) error
	FindResourceNode(ctx context.Context, id economy.NodeID) (economy.ResourceNode, error)
	ListProductionJobs(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error)
	ListDueProductionJobs(ctx context.Context, now time.Time, limit int) ([]economy.ProductionJob, error)
	SaveProductionJob(ctx context.Context, job economy.ProductionJob) error
	FindProductionJob(ctx context.Context, id economy.ProductionJobID) (economy.ProductionJob, error)
}

type AllianceRepository interface {
	Create(ctx context.Context, item alliance.Alliance) error
	FindByID(ctx context.Context, id alliance.ID) (alliance.Alliance, error)
	FindByPlayer(ctx context.Context, playerID player.ID) (alliance.Alliance, alliance.Membership, error)
	ListMembers(ctx context.Context, id alliance.ID) ([]alliance.Membership, error)
	SaveMembership(ctx context.Context, item alliance.Membership) error
	DeleteMembership(ctx context.Context, allianceID alliance.ID, playerID player.ID) error
	CreateInvite(ctx context.Context, item alliance.Invite) error
	FindInvite(ctx context.Context, id alliance.InviteID) (alliance.Invite, error)
	ListInvitesForPlayer(ctx context.Context, playerID player.ID) ([]alliance.Invite, error)
	UpdateInvite(ctx context.Context, item alliance.Invite) error
	AddTreasuryEntry(ctx context.Context, item alliance.TreasuryEntry) error
	ListTreasury(ctx context.Context, id alliance.ID, limit int) ([]alliance.TreasuryEntry, error)
	SaveBuff(ctx context.Context, item alliance.Buff) error
	ListBuffs(ctx context.Context, id alliance.ID) ([]alliance.Buff, error)
	AddTerritoryAid(ctx context.Context, item alliance.TerritoryAid) error
	ListTerritoryAid(ctx context.Context, id alliance.ID) ([]alliance.TerritoryAid, error)
}

type ChatRepository interface {
	AddMessage(ctx context.Context, item chat.Message) error
	ListMessages(ctx context.Context, playerID player.ID, channel chat.Channel, allianceID alliance.ID, limit int) ([]chat.Message, error)
}

type MarketRepository interface {
	CreateOrder(ctx context.Context, item market.Order) error
	FindOrder(ctx context.Context, id market.OrderID) (market.Order, error)
	UpdateOrder(ctx context.Context, item market.Order) error
	ListOrders(ctx context.Context, status market.Status, limit int) ([]market.Order, error)
}

type MonsterRepository interface {
	Create(ctx context.Context, item monster.Monster) error
	FindByID(ctx context.Context, id monster.ID) (monster.Monster, error)
	ListByMap(ctx context.Context, mapID string) ([]monster.Monster, error)
	ListActiveForTick(ctx context.Context, mapID string, limit int) ([]monster.Monster, error)
	ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.Monster, error)
	Update(ctx context.Context, item monster.Monster) error
	UpdateIfCurrent(ctx context.Context, previous, next monster.Monster) (bool, error)
	CountAliveBySpawn(ctx context.Context, mapID string) (map[monster.SpawnID]int, error)
	ListSpawnPoints(ctx context.Context, mapID string) ([]monster.SpawnPoint, error)
	SaveSpawnPoint(ctx context.Context, item monster.SpawnPoint) error
	CreateLootDrop(ctx context.Context, item monster.LootDrop) error
	FindLootDrop(ctx context.Context, id monster.LootDropID) (monster.LootDrop, error)
	ListLootDropsByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.LootDrop, error)
	ClaimLootDrop(ctx context.Context, id monster.LootDropID, playerID player.ID, now time.Time) (monster.LootDrop, error)
	AddEvent(ctx context.Context, item monster.Event) error
}

type ActionRepository interface {
	Append(ctx context.Context, item action.GameAction) error
	AppendUnique(ctx context.Context, item action.GameAction) (bool, error)
	HasIdempotencyKey(ctx context.Context, key string) (bool, error)
	ListPendingWeapons(ctx context.Context, playerID player.ID) ([]action.GameAction, error)
	ListRaids(ctx context.Context, playerID player.ID) ([]action.GameAction, error)
	HasRecentRaid(ctx context.Context, playerID player.ID, targetID building.ID, since time.Time) (bool, error)
	FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) ([]action.GameAction, error)
	MarkDone(ctx context.Context, id action.ID, now time.Time) error
	MarkFailed(ctx context.Context, id action.ID, message string, retryAt time.Time, now time.Time) error
}

type OutboxRepository interface {
	Append(ctx context.Context, item outbox.OutboxEvent) error
	FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) ([]outbox.OutboxEvent, error)
	MarkSent(ctx context.Context, id outbox.ID, now time.Time) error
	MarkFailed(ctx context.Context, id outbox.ID, message string, retryAt time.Time, now time.Time) error
	MarkDead(ctx context.Context, id outbox.ID, message string, now time.Time) error
	PruneSent(ctx context.Context, before time.Time, limit int) (int, error)
}

type UnitOfWork interface {
	Do(ctx context.Context, fn func(context.Context) error) error
}
