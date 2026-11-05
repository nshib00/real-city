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
	StateRepairing    State = "repairing"
	StateActive       State = "active"
	StateDamaged      State = "damaged"
	StateRuined       State = "ruined"
	StateConstruction State = StateBuilding
)

const (
	TypeTownHall                 Type = "town_hall"
	TypeDugout                   Type = "dugout"
	TypeWoodHouse                Type = "wood_house"
	TypeStoneHouse               Type = "stone_house"
	TypeApartmentHouse           Type = "apartment_house"
	TypeVilla                    Type = "villa"
	TypePalace                   Type = "palace"
	TypeResidentialSky           Type = "residential_skyscraper"
	TypeWorkshop                 Type = "workshop"
	TypeBrickKiln                Type = "brick_kiln"
	TypeBrickYard                Type = "brick_yard"
	TypeGlassWorkshop            Type = "glass_workshop"
	TypeForge                    Type = "forge"
	TypeWeavingYard              Type = "weaving_yard"
	TypeDyeWorks                 Type = "dye_works"
	TypeMechanicalShop           Type = "mechanical_workshop"
	TypeOpticalShop              Type = "optical_workshop"
	TypeMint                     Type = "mint"
	TypeCoinStorage              Type = "coin_storage"
	TypeMarket                   Type = "market"
	TypeTower                    Type = "tower"
	TypeDefenseCannon            Type = "defense_cannon"
	TypeDefenseStakes            Type = "defense_stakes"
	TypeDefenseResinSnare        Type = "defense_resin_snare"
	TypeDefenseBoltThrower       Type = "defense_bolt_thrower"
	TypeDefenseStormCoil         Type = "defense_storm_coil"
	TypeDefenseAutomatonBay      Type = "defense_automaton_bay"
	TypeDefenseGuardianEnclosure Type = "defense_guardian_enclosure"
	TypeWoodenWall               Type = "wooden_wall"
	TypeStoneWall                Type = "stone_wall"
	TypeConcreteWall             Type = "concrete_wall"
	TypeModernWall               Type = "modern_wall"
	TypeRoad                     Type = "road"
	TypeStandardRoad             Type = "standard_road"
	TypePavedRoad                Type = "paved_road"
	TypeAllianceHouse            Type = "alliance_house"
	TypeFieldBed                 Type = "field_bed"
	TypeSeedGarden               Type = "seed_garden"
	TypeHerbBed                  Type = "herb_bed"
	TypeMushroomGrove            Type = "mushroom_grove"
	TypeFlaxField                Type = "flax_field"
	TypeReedBed                  Type = "reed_bed"
	TypeDyeGarden                Type = "dye_garden"
	TypeOilseedField             Type = "oilseed_field"
	TypeSugarBed                 Type = "sugar_bed"
	TypeCrystalGreen             Type = "crystal_greenhouse"
	TypeLumberYard               Type = "lumber_yard"
	TypeSandQuarry               Type = "sand_quarry"
	TypeMine                     Type = "mine"
	TypeClayQuarry               Type = "clay_quarry"
	TypeIronMine                 Type = "iron_mine"
	TypeCopperMine               Type = "copper_mine"
	TypeResinKiln                Type = "resin_kiln"
	TypeSulfurSpring             Type = "sulfur_spring"
	TypeOilWell                  Type = "oil_well"
	TypeStoneCutters             Type = "stone_cutters"
	TypeTileFactory              Type = "tile_factory"
	TypeCementWorkshop           Type = "cement_workshop"
	TypeConcretePlant            Type = "concrete_plant"
	TypeRopeYard                 Type = "rope_yard"
	TypePaperWorkshop            Type = "paper_workshop"
	TypePaintWorkshop            Type = "paint_workshop"
	TypeOilPress                 Type = "oil_press"
	TypeFoundry                  Type = "foundry"
	TypeSteelworks               Type = "steelworks"
	TypeElectronics              Type = "electronics_workshop"
	TypeOilRefinery              Type = "oil_refinery"
	TypeChemicalShop             Type = "chemical_workshop"
	TypeMilitaryPlant            Type = "military_factory"
	TypePrecisionShop            Type = "precision_workshop"
	TypeSiegeYard                Type = "siege_yard"
	TypeResonanceLaboratory      Type = "resonance_laboratory"
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
	ID                       ID
	MapID                    string
	OwnerID                  string
	Type                     Type
	Name                     string
	Level                    int
	State                    State
	Health                   int
	Tile                     world.Coord
	Footprint                Footprint
	Rotation                 int
	StartedAt                time.Time
	CompletesAt              *time.Time
	FieldStage               int
	FieldStageStartedAt      *time.Time
	FieldStageReadyAt        *time.Time
	FieldSuperCrop           bool
	CreatedAt                time.Time
	UpdatedAt                time.Time
	CannonEnabled            bool
	TowerWatchkeeperAssigned bool
	CannonNextAttackAt       *time.Time
	CannonTargetID           string
	TrapCharges              int
}

func (b Building) IsRoad() bool {
	return b.Type == TypeRoad || b.Type == TypeStandardRoad || b.Type == TypePavedRoad
}

func (b Building) CountsTowardLimit() bool {
	return !IsLimitFreeType(b.Type) && b.State != StateRuined
}

func IsLimitFreeType(t Type) bool {
	return t == TypeRoad ||
		t == TypeDefenseStakes ||
		t == TypeDefenseResinSnare ||
		t == TypeStandardRoad ||
		t == TypePavedRoad ||
		t == TypeWoodenWall ||
		t == TypeStoneWall ||
		t == TypeConcreteWall ||
		t == TypeModernWall
}

func IsTrapType(t Type) bool {
	return t == TypeDefenseStakes || t == TypeDefenseResinSnare
}

func IsRoadType(t Type) bool {
	return t == TypeRoad || t == TypeStandardRoad || t == TypePavedRoad
}

func (b Building) OccupiedTiles() []world.Coord {
	width := max(1, b.Footprint.Width)
	height := max(1, b.Footprint.Height)
	tiles := make([]world.Coord, 0, width*height)
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			tiles = append(tiles, world.NormalizeCoord(world.Coord{X: b.Tile.X + x, Y: b.Tile.Y + y}))
		}
	}
	return tiles
}
