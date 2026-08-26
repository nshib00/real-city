package catalog

import "real-city/backend/internal/domain/building"

var HousingChain = map[building.Type][]building.Type{
	building.TypeDugout:         {building.TypeWoodHouse},
	building.TypeWoodHouse:      {building.TypeStoneHouse},
	building.TypeStoneHouse:     {building.TypeApartmentHouse, building.TypeVilla},
	building.TypeApartmentHouse: {building.TypeResidentialSky},
	building.TypeVilla:          {building.TypePalace},
}

var WallChain = map[building.Type]struct {
	Levels int
	Next   building.Type
}{
	building.TypeWoodenWall:   {Levels: 3, Next: building.TypeStoneWall},
	building.TypeStoneWall:    {Levels: 4, Next: building.TypeConcreteWall},
	building.TypeConcreteWall: {Levels: 3, Next: building.TypeModernWall},
	building.TypeModernWall:   {Levels: 5},
}
