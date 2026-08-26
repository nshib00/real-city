package service

import (
	"context"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type ResourceService struct {
	repo    EconomyRepository
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
	events  *EventBus
}

func NewResourceService(repo EconomyRepository, economyService *EconomyService, log *slog.Logger) *ResourceService {
	return &ResourceService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *ResourceService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *ResourceService) List(ctx context.Context) ([]economy.ResourceNode, error) {
	nodes, err := s.repo.ListResourceNodes(ctx, DefaultWorldID)
	if err != nil {
		return nil, err
	}
	now := s.now()
	for index, node := range nodes {
		if node.State == economy.NodeDepleted && node.RespawnAt != nil && !node.RespawnAt.After(now) {
			node.Amount = node.MaxAmount
			node.State = economy.NodeNeutral
			node.RespawnAt = nil
			node.OwnerID = ""
			node.UpdatedAt = now
			if err := s.repo.SaveResourceNode(ctx, node); err != nil {
				return nil, err
			}
			s.publish(node)
			nodes[index] = node
		}
	}
	return nodes, nil
}

func (s *ResourceService) Claim(ctx context.Context, id economy.NodeID, playerID player.ID) (economy.ResourceNode, error) {
	node, err := s.repo.FindResourceNode(ctx, id)
	if err != nil {
		return economy.ResourceNode{}, err
	}
	if node.State == economy.NodeDepleted {
		return economy.ResourceNode{}, apperror.New(apperror.Conflict, "resource node is depleted")
	}
	node.State = economy.NodeClaimed
	node.OwnerID = string(playerID)
	node.UpdatedAt = s.now()
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return economy.ResourceNode{}, err
	}
	s.publish(node)
	s.log.Info("economy.resource_node.claimed", "event", "economy.resource_node.claimed", "node_id", node.ID, "player_id", playerID, "resource", node.Resource)
	return node, nil
}

func (s *ResourceService) Harvest(ctx context.Context, id economy.NodeID, playerID player.ID) (economy.ResourceNode, economy.Inventory, error) {
	node, err := s.repo.FindResourceNode(ctx, id)
	if err != nil {
		return economy.ResourceNode{}, economy.Inventory{}, err
	}
	if node.State == economy.NodeDepleted || node.Amount <= 0 {
		return economy.ResourceNode{}, economy.Inventory{}, apperror.New(apperror.Conflict, "resource node is depleted")
	}
	if node.OwnerID != "" && node.OwnerID != string(playerID) {
		return economy.ResourceNode{}, economy.Inventory{}, apperror.New(apperror.Forbidden, "resource node belongs to another player")
	}
	harvest := min(12, node.Amount)
	node.Amount -= harvest
	if node.Amount == 0 {
		respawn := s.now().Add(20 * time.Minute)
		node.State = economy.NodeDepleted
		node.RespawnAt = &respawn
	} else {
		node.State = economy.NodeClaimed
		node.OwnerID = string(playerID)
	}
	node.UpdatedAt = s.now()
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return economy.ResourceNode{}, economy.Inventory{}, err
	}
	inventory, _, err := s.economy.Add(ctx, playerID, []economy.ResourceAmount{{Resource: node.Resource, Amount: harvest}}, "harvest")
	if err != nil {
		return economy.ResourceNode{}, economy.Inventory{}, err
	}
	s.publish(node)
	s.log.Info("economy.resource.harvested", "event", "economy.resource.harvested", "node_id", node.ID, "player_id", playerID, "resource", node.Resource, "amount", harvest)
	return node, inventory, nil
}

func (s *ResourceService) publish(node economy.ResourceNode) {
	if s.events == nil {
		return
	}
	s.events.Publish(Event{
		Type:     EventResourceChanged,
		ChunkID:  world.ChunkID(node.MapID, world.ChunkForTile(node.Tile)),
		PlayerID: player.ID(node.OwnerID),
		Payload:  ResourceChangedPayload{Node: node},
	})
}
