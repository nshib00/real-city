package economy

import (
	"time"

	"real-city/backend/internal/domain/world"
)

type ResourceType string
type NodeID string
type ProductionJobID string
type TransactionID string
type NodeState string
type ProductionState string
type TransactionKind string

const (
	ResourceCoins          ResourceType = "coins"
	ResourcePopulation     ResourceType = "population"
	ResourceAeolianCrystal ResourceType = "aeolian-crystal"
	ResourceWood           ResourceType = "wood"
	ResourceStone          ResourceType = "stone"
	ResourceClay           ResourceType = "clay"
	ResourceSand           ResourceType = "sand"
	ResourceCoal           ResourceType = "coal"
	ResourceIronOre        ResourceType = "iron_ore"
	ResourceCopper         ResourceType = "copper"
	ResourceResin          ResourceType = "resin"
	ResourceFlax           ResourceType = "flax"
	ResourceWindleaf       ResourceType = "windleaf"
	ResourceHerbs          ResourceType = "herbs"
	ResourceMushrooms      ResourceType = "mushrooms"
	ResourceSeeds          ResourceType = "seeds"
	ResourceBrick          ResourceType = "brick"
	ResourceStoneBlock     ResourceType = "stone_block"
	ResourceMetal          ResourceType = "metal"
	ResourceIron           ResourceType = "iron"
	ResourceSteel          ResourceType = "steel"
	ResourceGlass          ResourceType = "glass"
	ResourcePlanks         ResourceType = "planks"
	ResourcePremiumPlanks  ResourceType = "premium_planks"
	ResourceRope           ResourceType = "rope"
	ResourceCopperParts    ResourceType = "copper_parts"
	ResourceIronIngot      ResourceType = "iron_ingot"
	ResourceGoldIngot      ResourceType = "gold_ingot"
	ResourceCement         ResourceType = "cement"
	ResourceConcrete       ResourceType = "concrete"
	ResourceReinforcedConc ResourceType = "reinforced_concrete"
	ResourceFabric         ResourceType = "fabric"
	ResourceMechanism      ResourceType = "mechanism"
	ResourceSuperMechanism ResourceType = "super_mechanism"
	ResourceElectronics    ResourceType = "electronics"
	ResourceSulfur         ResourceType = "sulfur"
	ResourceExplosives     ResourceType = "explosives"
	ResourceOil            ResourceType = "oil"
	ResourceFuel           ResourceType = "fuel"
	ResourceSuperSeeds     ResourceType = "super-seeds"
	ResourceSuperFiber     ResourceType = "super-fiber"
	ResourceSuperMushrooms ResourceType = "super-mushrooms"
	ResourceSuperWindleaf  ResourceType = "super-windleaf"
	ResourceEmeraldDust    ResourceType = "emerald_dust"
	ResourceElderwoodHeart ResourceType = "elderwood-heart"
	ResourceRuneTile       ResourceType = "rune_tile"
)

const (
	NodeNeutral  NodeState = "neutral"
	NodeClaimed  NodeState = "claimed"
	NodeDepleted NodeState = "depleted"

	ProductionRunning   ProductionState = "running"
	ProductionCompleted ProductionState = "completed"
	ProductionCancelled ProductionState = "cancelled"

	TransactionAdd     TransactionKind = "add"
	TransactionSpend   TransactionKind = "spend"
	TransactionHarvest TransactionKind = "harvest"
	TransactionReserve TransactionKind = "reserve"
)

type ResourceAmount struct {
	Resource ResourceType
	Amount   int
}

type Inventory struct {
	PlayerID     string
	Items        map[ResourceType]int
	CoinCapacity int
	UpdatedAt    time.Time
}

type StorageLimit struct {
	Resource ResourceType
	Capacity int
}

type ProductionRecipe struct {
	ID              string
	Name            string
	BuildingType    string
	Duration        time.Duration
	Workers         int
	Input           []ResourceAmount
	Output          []ResourceAmount
	FuelPerRun      int
	RequiredLevel   int
	AutoCollectable bool
}

type ProductionJob struct {
	ID          ProductionJobID
	PlayerID    string
	BuildingID  string
	RecipeID    string
	State       ProductionState
	StartedAt   time.Time
	CompletesAt time.Time
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

type ResourceNode struct {
	ID        NodeID
	MapID     string
	Type      string
	Resource  ResourceType
	Amount    int
	MaxAmount int
	Tile      world.Coord
	State     NodeState
	OwnerID   string
	RespawnAt *time.Time
	CreatedAt time.Time
	UpdatedAt time.Time
}

type Transaction struct {
	ID        TransactionID
	PlayerID  string
	Kind      TransactionKind
	Resource  ResourceType
	Amount    int
	Reason    string
	CreatedAt time.Time
}

func NewInventory(playerID string, now time.Time, coinCapacity int) Inventory {
	return Inventory{
		PlayerID:     playerID,
		Items:        StartingItems(),
		CoinCapacity: coinCapacity,
		UpdatedAt:    now,
	}
}

func EmptyInventory(playerID string, now time.Time, coinCapacity int) Inventory {
	return Inventory{
		PlayerID:     playerID,
		Items:        map[ResourceType]int{},
		CoinCapacity: coinCapacity,
		UpdatedAt:    now,
	}
}

func StartingItems() map[ResourceType]int {
	return map[ResourceType]int{
		ResourceCoins:          1250,
		ResourcePopulation:     18,
		ResourceAeolianCrystal: 18,
		ResourceWood:           420,
		ResourceStone:          260,
		ResourceClay:           120,
		ResourceSand:           90,
		ResourceCoal:           44,
		ResourceIronOre:        38,
		ResourceCopper:         22,
		ResourceResin:          16,
		ResourceFlax:           3,
		ResourceWindleaf:       27,
		ResourceHerbs:          31,
		ResourceMushrooms:      9,
		ResourceSeeds:          64,
		ResourceBrick:          160,
		ResourceStoneBlock:     11,
		ResourceMetal:          58,
		ResourceIron:           34,
		ResourceSteel:          12,
		ResourceGlass:          32,
		ResourcePlanks:         88,
		ResourcePremiumPlanks:  0,
		ResourceRope:           0,
		ResourceCopperParts:    0,
		ResourceIronIngot:      0,
		ResourceGoldIngot:      0,
		ResourceCement:         26,
		ResourceConcrete:       14,
		ResourceReinforcedConc: 0,
		ResourceFabric:         18,
		ResourceMechanism:      0,
		ResourceSuperMechanism: 0,
		ResourceElectronics:    3,
		ResourceSulfur:         7,
		ResourceExplosives:     0,
		ResourceOil:            36,
		ResourceFuel:           12,
		ResourceSuperSeeds:     3,
		ResourceSuperFiber:     0,
		ResourceSuperMushrooms: 1,
		ResourceSuperWindleaf:  0,
		ResourceEmeraldDust:    0,
		ResourceElderwoodHeart: 0,
		ResourceRuneTile:       0,
	}
}

func (i Inventory) Has(cost []ResourceAmount) bool {
	for _, item := range cost {
		if i.Items[item.Resource] < item.Amount {
			return false
		}
	}
	return true
}

func (i *Inventory) Spend(cost []ResourceAmount, now time.Time) bool {
	if !i.Has(cost) {
		return false
	}
	for _, item := range cost {
		i.Items[item.Resource] -= item.Amount
	}
	i.UpdatedAt = now
	return true
}

func (i *Inventory) Add(items []ResourceAmount, now time.Time) []ResourceAmount {
	overflow := make([]ResourceAmount, 0)
	for _, item := range items {
		if item.Amount <= 0 {
			continue
		}
		if item.Resource == ResourceCoins && i.CoinCapacity > 0 {
			next := i.Items[item.Resource] + item.Amount
			if next > i.CoinCapacity {
				overflow = append(overflow, ResourceAmount{Resource: item.Resource, Amount: next - i.CoinCapacity})
				next = i.CoinCapacity
			}
			i.Items[item.Resource] = next
			continue
		}
		i.Items[item.Resource] += item.Amount
	}
	i.UpdatedAt = now
	return overflow
}
