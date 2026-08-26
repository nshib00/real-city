package building

import (
	"time"

	"real-city/backend/internal/domain/world"
)

type ID string
type Type string
type State string

const (
	StatePlanned      State = "planned"
	StateBuilding     State = "building"
	StateActive       State = "active"
	StateDamaged      State = "damaged"
	StateRuined       State = "ruined"
	StateConstruction State = StateBuilding
)

const (
	TypeTownHall       Type = "town_hall"
	TypeDugout         Type = "dugout"
	TypeWoodHouse      Type = "wood_house"
	TypeStoneHouse     Type = "stone_house"
	TypeApartmentHouse Type = "apartment_house"
	TypeVilla          Type = "villa"
	TypePalace         Type = "palace"
	TypeResidentialSky Type = "residential_skyscraper"
	TypeWorkshop       Type = "workshop"
	TypeWarehouse      Type = "warehouse"
	TypeCoinStorage    Type = "coin_storage"
	TypeMarket         Type = "market"
	TypeTower          Type = "tower"
	TypeWoodenWall     Type = "wooden_wall"
	TypeStoneWall      Type = "stone_wall"
	TypeConcreteWall   Type = "concrete_wall"
	TypeModernWall     Type = "modern_wall"
	TypeRoad           Type = "road"
	TypeAllianceHouse  Type = "alliance_house"
	TypeFieldBed       Type = "field_bed"
	TypeLumberYard     Type = "lumber_yard"
	TypeStoneCutters   Type = "stone_cutters"
	TypeOilRefinery    Type = "oil_refinery"
)

type Footprint struct {
	Width  int
	Height int
}

type Cost struct {
	Resource string
	Amount   int
}

type Building struct {
	ID          ID
	MapID       string
	OwnerID     string
	Type        Type
	Name        string
	Level       int
	State       State
	Health      int
	Tile        world.Coord
	Footprint   Footprint
	StartedAt   time.Time
	CompletesAt *time.Time
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

func (b Building) IsRoad() bool {
	return b.Type == TypeRoad
}

func (b Building) OccupiedTiles() []world.Coord {
	width := max(1, b.Footprint.Width)
	height := max(1, b.Footprint.Height)
	tiles := make([]world.Coord, 0, width*height)
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			tiles = append(tiles, world.Coord{X: b.Tile.X + x, Y: b.Tile.Y + y})
		}
	}
	return tiles
}
