package service

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type ResourceService struct {
	repo       EconomyRepository
	economy    *EconomyService
	log        *slog.Logger
	now        func() time.Time
	events     *EventBus
	actions    ActionRepository
	experience *ExperienceService
	worlds     WorldRepository
	buildings  BuildingRepository
	randomIntn func(int) int
}

func NewResourceService(repo EconomyRepository, economyService *EconomyService, log *slog.Logger) *ResourceService {
	return &ResourceService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }, randomIntn: rand.Intn}
}

func (s *ResourceService) SetOilWorld(worlds WorldRepository, buildings BuildingRepository) {
	s.worlds, s.buildings = worlds, buildings
}

func (s *ResourceService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *ResourceService) SetActionQueue(actions ActionRepository) {
	s.actions = actions
}

func (s *ResourceService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *ResourceService) List(ctx context.Context) ([]economy.ResourceNode, error) {
	nodes, err := s.repo.ListResourceNodes(ctx, DefaultWorldID)
	if err != nil {
		return nil, err
	}
	now := s.now()
	for index, node := range nodes {
		if node.Resource == economy.ResourceOil || node.State != economy.NodeDepleted || node.RespawnAt == nil || node.RespawnAt.After(now) {
			continue
		}
		node.Amount, node.State, node.RespawnAt, node.OwnerID, node.UpdatedAt = node.MaxAmount, economy.NodeNeutral, nil, "", now
		if err := s.repo.SaveResourceNode(ctx, node); err != nil {
			return nil, err
		}
		s.publish(node)
		nodes[index] = node
	}
	return nodes, nil
}

func (s *ResourceService) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	nodes, err := s.repo.ListResourceNodes(ctx, DefaultWorldID)
	if err != nil {
		return 0, err
	}
	restored := 0
	processed := 0
	for _, node := range nodes {
		if limit > 0 && processed >= limit {
			break
		}
		if node.Resource == economy.ResourceOil && s.worlds != nil && s.buildings != nil {
			changed, err := s.tickOil(ctx, node, now)
			if err != nil {
				return restored, err
			}
			if changed {
				processed++
				if node.State == economy.NodeDepleted && node.RespawnAt != nil && !node.RespawnAt.After(now) {
					restored++
				}
			}
			continue
		}
		if node.State != economy.NodeDepleted || node.RespawnAt == nil || node.RespawnAt.After(now) {
			continue
		}
		node.Amount = node.MaxAmount
		node.State = economy.NodeNeutral
		node.OwnerID = ""
		node.RespawnAt = nil
		node.UpdatedAt = now
		if err := s.repo.SaveResourceNode(ctx, node); err != nil {
			return restored, err
		}
		s.publish(node)
		s.log.Info("simulation.resource.respawned", "event", "simulation.resource.respawned", "node_id", node.ID, "resource", node.Resource, "chunk_id", world.ChunkID(node.MapID, world.ChunkForTile(node.Tile)))
		restored++
		processed++
	}
	return restored, nil
}

func (s *ResourceService) Claim(ctx context.Context, id economy.NodeID, playerID player.ID) (economy.ResourceNode, error) {
	node, err := s.repo.FindResourceNode(ctx, id)
	if err != nil {
		return economy.ResourceNode{}, err
	}
	if node.Resource == economy.ResourceOil {
		return economy.ResourceNode{}, apperror.New(apperror.Conflict, "нефть захватывается при строительстве вышки")
	}
	if node.State == economy.NodeDepleted {
		return economy.ResourceNode{}, apperror.New(apperror.Conflict, "resource node is depleted")
	}
	firstClaim := node.OwnerID == ""
	node.State = economy.NodeClaimed
	node.OwnerID = string(playerID)
	node.UpdatedAt = s.now()
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return economy.ResourceNode{}, err
	}
	if firstClaim && s.experience != nil {
		if err := s.experience.Award(ctx, playerID, 5, "resource:claim", "resource:"+string(id)+":first_claim"); err != nil {
			return economy.ResourceNode{}, err
		}
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
	if node.Resource == economy.ResourceOil {
		return economy.ResourceNode{}, economy.Inventory{}, apperror.New(apperror.Conflict, "нефть добывается циклом нефтяной вышки")
	}
	if node.State == economy.NodeDepleted || node.Amount <= 0 {
		return economy.ResourceNode{}, economy.Inventory{}, apperror.New(apperror.Conflict, "resource node is depleted")
	}
	if node.OwnerID != "" && node.OwnerID != string(playerID) {
		return economy.ResourceNode{}, economy.Inventory{}, apperror.New(apperror.Forbidden, "resource node belongs to another player")
	}
	harvestKey := fmt.Sprintf("resource:%s:harvest:%d:%d", id, node.UpdatedAt.UnixNano(), node.Amount)
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
	if node.RespawnAt != nil {
		_ = s.scheduleRespawn(ctx, node)
	}
	inventory, _, err := s.economy.Add(ctx, playerID, []economy.ResourceAmount{{Resource: node.Resource, Amount: harvest}}, "harvest")
	if err != nil {
		return economy.ResourceNode{}, economy.Inventory{}, err
	}
	if s.experience != nil {
		if err := s.experience.Award(ctx, playerID, 1, "resource:harvest", harvestKey); err != nil {
			return economy.ResourceNode{}, economy.Inventory{}, err
		}
	}
	s.publish(node)
	s.log.Info("economy.resource.harvested", "event", "economy.resource.harvested", "node_id", node.ID, "player_id", playerID, "resource", node.Resource, "amount", harvest)
	return node, inventory, nil
}

func (s *ResourceService) scheduleRespawn(ctx context.Context, node economy.ResourceNode) error {
	if s.actions == nil || node.RespawnAt == nil {
		return nil
	}
	now := s.now()
	return s.actions.Append(ctx, action.NewGameAction(
		action.ID(fmt.Sprintf("act_resource_%s_%d", node.ID, node.RespawnAt.UnixNano())),
		action.TypeRespawnResource,
		fmt.Sprintf("resource:%s:respawn:%d", node.ID, node.RespawnAt.UnixNano()),
		action.ObjectRef{},
		action.ObjectRef{ID: string(node.ID), Type: "resource_node"},
		*node.RespawnAt,
		now,
	))
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
