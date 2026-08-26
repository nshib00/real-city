package service

import (
	"context"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

type PlayerRepository interface {
	Create(ctx context.Context, p player.Player) error
	FindByID(ctx context.Context, id player.ID) (player.Player, error)
	FindByEmail(ctx context.Context, email string) (player.Player, error)
	UpdateProfile(ctx context.Context, id player.ID, profile player.Profile) (player.Player, error)
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
	UpdateTile(ctx context.Context, tile world.Tile) error
}

type BuildingRepository interface {
	Create(ctx context.Context, b building.Building) error
	FindByID(ctx context.Context, id building.ID) (building.Building, error)
	ListByPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error)
	ListByChunk(ctx context.Context, mapID string, coord world.ChunkCoord) ([]building.Building, error)
	Update(ctx context.Context, b building.Building) error
	Delete(ctx context.Context, id building.ID) error
}

type EconomyRepository interface {
	GetInventory(ctx context.Context, playerID player.ID, coinCapacity int) (economy.Inventory, error)
	SaveInventory(ctx context.Context, inventory economy.Inventory) error
	AddTransaction(ctx context.Context, tx economy.Transaction) error
	ListTransactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error)
	ListResourceNodes(ctx context.Context, mapID string) ([]economy.ResourceNode, error)
	SaveResourceNode(ctx context.Context, node economy.ResourceNode) error
	FindResourceNode(ctx context.Context, id economy.NodeID) (economy.ResourceNode, error)
	ListProductionJobs(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error)
	SaveProductionJob(ctx context.Context, job economy.ProductionJob) error
	FindProductionJob(ctx context.Context, id economy.ProductionJobID) (economy.ProductionJob, error)
}
