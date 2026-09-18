package catalog

import (
	"time"

	"real-city/backend/internal/domain/building"
)

type BuildingType struct {
	Type              building.Type
	Category          string
	Name              string
	Level             int
	Footprint         building.Footprint
	BuildDuration     time.Duration
	Population        int
	Health            int
	Cost              []building.Cost
	RequiresTownHall  bool
	CountsTowardLimit bool
	UpgradeTo         []building.Type
	UpgradeLevels     []BuildingUpgradeLevel
}

type BuildingUpgradeLevel struct {
	Level         int
	BuildDuration time.Duration
	Population    int
	Health        int
	Cost          []building.Cost
	NextType      building.Type
}

var Buildings = map[building.Type]BuildingType{
	building.TypeTownHall: {
		Type:              building.TypeTownHall,
		Category:          "center",
		Name:              "Ратуша",
		Level:             1,
		Footprint:         building.Footprint{Width: 1, Height: 1},
		BuildDuration:     0,
		Health:            100,
		CountsTowardLimit: true,
		UpgradeLevels: []BuildingUpgradeLevel{
			{Level: 1, BuildDuration: 0, Health: 100},
			{Level: 2, BuildDuration: 90 * time.Second, Health: 220, Cost: []building.Cost{{Resource: "coins", Amount: 1500}, {Resource: "wood", Amount: 40}, {Resource: "windleaf", Amount: 2}}},
			{Level: 3, BuildDuration: 260 * time.Second, Health: 480, Cost: []building.Cost{{Resource: "coins", Amount: 5300}, {Resource: "wood", Amount: 92}, {Resource: "windleaf", Amount: 6}, {Resource: "glass", Amount: 1}}},
			{Level: 4, BuildDuration: 1025 * time.Second, Health: 910, Cost: []building.Cost{{Resource: "coins", Amount: 12000}, {Resource: "wood", Amount: 213}, {Resource: "mushrooms", Amount: 3}, {Resource: "planks", Amount: 17}, {Resource: "glass", Amount: 4}}},
			{Level: 5, BuildDuration: 2170 * time.Second, Health: 1230, Cost: []building.Cost{{Resource: "coins", Amount: 34000}, {Resource: "wood", Amount: 567}, {Resource: "mushrooms", Amount: 10}, {Resource: "planks", Amount: 48}, {Resource: "glass", Amount: 12}}},
			{Level: 6, BuildDuration: 3750 * time.Second, Health: 1520, Cost: []building.Cost{{Resource: "coins", Amount: 78000}, {Resource: "wood", Amount: 1200}, {Resource: "mushrooms", Amount: 27}, {Resource: "planks", Amount: 81}, {Resource: "stone", Amount: 34}}},
			{Level: 7, BuildDuration: 8580 * time.Second, Health: 1890, Cost: []building.Cost{{Resource: "coins", Amount: 145000}, {Resource: "planks", Amount: 195}, {Resource: "stone", Amount: 78}, {Resource: "stone_block", Amount: 25}}},
			{Level: 8, BuildDuration: 13500 * time.Second, Health: 2360, Cost: []building.Cost{{Resource: "coins", Amount: 286000}, {Resource: "planks", Amount: 425}, {Resource: "stone_block", Amount: 52}, {Resource: "brick", Amount: 16}}},
			{Level: 9, BuildDuration: 18840 * time.Second, Health: 2910, Cost: []building.Cost{{Resource: "coins", Amount: 527000}, {Resource: "stone_block", Amount: 121}, {Resource: "brick", Amount: 45}, {Resource: "glass", Amount: 47}}},
			{Level: 10, BuildDuration: 27360 * time.Second, Health: 3530, Cost: []building.Cost{{Resource: "coins", Amount: 875000}, {Resource: "brick", Amount: 109}, {Resource: "premium_planks", Amount: 4}, {Resource: "super-mushrooms", Amount: 2}, {Resource: "glass", Amount: 78}}},
		},
	},
	building.TypeDugout:         {Type: building.TypeDugout, Category: "housing", Name: "Землянка", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 10 * time.Second, Population: 1, Health: 35, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 50}, {Resource: "wood", Amount: 3}}, UpgradeTo: []building.Type{building.TypeWoodHouse}, UpgradeLevels: []BuildingUpgradeLevel{{Level: 1, BuildDuration: 10 * time.Second, Population: 1, Health: 35, Cost: []building.Cost{{Resource: "coins", Amount: 50}, {Resource: "wood", Amount: 3}}}, {Level: 2, BuildDuration: 45 * time.Second, Population: 2, Health: 140, Cost: []building.Cost{{Resource: "coins", Amount: 400}, {Resource: "wood", Amount: 10}}}, {Level: 3, BuildDuration: 170 * time.Second, Population: 3, Health: 270, Cost: []building.Cost{{Resource: "coins", Amount: 950}, {Resource: "wood", Amount: 23}, {Resource: "windleaf", Amount: 2}}}, {Level: 4, BuildDuration: 515 * time.Second, Population: 4, Health: 435, Cost: []building.Cost{{Resource: "coins", Amount: 2800}, {Resource: "wood", Amount: 40}, {Resource: "windleaf", Amount: 5}, {Resource: "planks", Amount: 2}}}, {Level: 5, BuildDuration: 1090 * time.Second, Population: 6, Health: 760, Cost: []building.Cost{{Resource: "coins", Amount: 6500}, {Resource: "wood", Amount: 82}, {Resource: "windleaf", Amount: 11}, {Resource: "planks", Amount: 4}}, NextType: building.TypeWoodHouse}}},
	building.TypeWoodHouse:      {Type: building.TypeWoodHouse, Category: "housing", Name: "Деревянный дом", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 2070 * time.Second, Population: 8, Health: 1200, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 10000}, {Resource: "planks", Amount: 20}, {Resource: "stone", Amount: 4}, {Resource: "glass", Amount: 1}}, UpgradeTo: []building.Type{building.TypeStoneHouse}, UpgradeLevels: []BuildingUpgradeLevel{{Level: 1, BuildDuration: 2070 * time.Second, Population: 8, Health: 1200, Cost: []building.Cost{{Resource: "coins", Amount: 10000}, {Resource: "planks", Amount: 20}, {Resource: "stone", Amount: 4}, {Resource: "glass", Amount: 1}}}, {Level: 2, BuildDuration: 3920 * time.Second, Population: 10, Health: 1750, Cost: []building.Cost{{Resource: "coins", Amount: 16400}, {Resource: "planks", Amount: 36}, {Resource: "stone", Amount: 7}, {Resource: "glass", Amount: 2}}}, {Level: 3, BuildDuration: 6090 * time.Second, Population: 12, Health: 2100, Cost: []building.Cost{{Resource: "coins", Amount: 24200}, {Resource: "planks", Amount: 56}, {Resource: "stone", Amount: 10}, {Resource: "glass", Amount: 4}}}, {Level: 4, BuildDuration: 8400 * time.Second, Population: 14, Health: 2550, Cost: []building.Cost{{Resource: "coins", Amount: 33300}, {Resource: "planks", Amount: 70}, {Resource: "stone", Amount: 14}, {Resource: "glass", Amount: 7}}}, {Level: 5, BuildDuration: 11700 * time.Second, Population: 17, Health: 2930, Cost: []building.Cost{{Resource: "coins", Amount: 43000}, {Resource: "planks", Amount: 95}, {Resource: "stone", Amount: 20}, {Resource: "glass", Amount: 10}}}, {Level: 6, BuildDuration: 14400 * time.Second, Population: 20, Health: 3310, Cost: []building.Cost{{Resource: "coins", Amount: 52500}, {Resource: "planks", Amount: 120}, {Resource: "stone", Amount: 25}, {Resource: "glass", Amount: 13}, {Resource: "stone_block", Amount: 4}}, NextType: building.TypeStoneHouse}}},
	building.TypeStoneHouse:     {Type: building.TypeStoneHouse, Category: "housing", Name: "Каменный дом", Level: 3, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 8 * time.Minute, Population: 4, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "stone", Amount: 120}, {Resource: "brick", Amount: 60}}, UpgradeTo: []building.Type{building.TypeApartmentHouse, building.TypeVilla}},
	building.TypeApartmentHouse: {Type: building.TypeApartmentHouse, Category: "housing", Name: "Многоквартирный дом", Level: 4, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 15 * time.Minute, Population: 8, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "brick", Amount: 240}}},
	building.TypeResidentialSky: {Type: building.TypeResidentialSky, Category: "housing", Name: "Жилой небоскреб", Level: 5, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 30 * time.Minute, Population: 14, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "metal", Amount: 220}, {Resource: "glass", Amount: 160}}},
	building.TypeVilla:          {Type: building.TypeVilla, Category: "housing", Name: "Вилла", Level: 4, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 18 * time.Minute, Population: 6, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "stone", Amount: 260}, {Resource: "glass", Amount: 80}}},
	building.TypePalace:         {Type: building.TypePalace, Category: "housing", Name: "Дворец", Level: 5, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 40 * time.Minute, Population: 10, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "brick", Amount: 520}, {Resource: "glass", Amount: 240}}},
	building.TypeWorkshop:       {Type: building.TypeWorkshop, Category: "industry", Name: "Мастерская", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 3 * time.Minute, Population: 3, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "wood", Amount: 90}, {Resource: "stone", Amount: 40}}},
	building.TypeWarehouse:      {Type: building.TypeWarehouse, Category: "storage", Name: "Склад материалов", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 2 * time.Minute, Population: 2, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "wood", Amount: 80}, {Resource: "stone", Amount: 30}}},
	building.TypeCoinStorage:    {Type: building.TypeCoinStorage, Category: "storage", Name: "Хранилище монет", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 2 * time.Minute, Population: 1, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "wood", Amount: 70}, {Resource: "stone", Amount: 40}}},
	building.TypeMarket:         {Type: building.TypeMarket, Category: "trade", Name: "Рынок", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 5 * time.Minute, Population: 4, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 400}, {Resource: "wood", Amount: 80}}},
	building.TypeTower:          {Type: building.TypeTower, Category: "defense", Name: "Сторожевая башня", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 4 * time.Minute, Population: 2, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "wood", Amount: 120}, {Resource: "stone", Amount: 80}}},
	building.TypeWoodenWall:     {Type: building.TypeWoodenWall, Category: "defense", Name: "Деревянная стена", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: time.Minute, Population: 1, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "wood", Amount: 50}}, UpgradeTo: []building.Type{building.TypeStoneWall}},
	building.TypeStoneWall:      {Type: building.TypeStoneWall, Category: "defense", Name: "Каменная стена", Level: 4, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 2 * time.Minute, Population: 1, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "stone", Amount: 120}, {Resource: "brick", Amount: 40}}, UpgradeTo: []building.Type{building.TypeConcreteWall}},
	building.TypeConcreteWall:   {Type: building.TypeConcreteWall, Category: "defense", Name: "Бетонная стена", Level: 8, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 3 * time.Minute, Population: 1, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "concrete", Amount: 120}, {Resource: "steel", Amount: 30}}, UpgradeTo: []building.Type{building.TypeModernWall}},
	building.TypeModernWall:     {Type: building.TypeModernWall, Category: "defense", Name: "Современная стена", Level: 11, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 5 * time.Minute, Population: 2, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "steel", Amount: 120}, {Resource: "electronics", Amount: 20}}},
	building.TypeRoad:           {Type: building.TypeRoad, Name: "Грунтовая дорога", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 30 * time.Second, RequiresTownHall: true, CountsTowardLimit: false, Cost: []building.Cost{{Resource: "coins", Amount: 10}}},
	building.TypeAllianceHouse:  {Type: building.TypeAllianceHouse, Name: "Союзный дом", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 5 * time.Minute, Population: 4, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 500}, {Resource: "brick", Amount: 120}}},
	building.TypeFieldBed:       {Type: building.TypeFieldBed, Category: "fields", Name: "Грядка ветролиста", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 40 * time.Second, Population: 1, Health: 70, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 300}, {Resource: "wood", Amount: 4}}, UpgradeLevels: []BuildingUpgradeLevel{{Level: 1, BuildDuration: 40 * time.Second, Population: 1, Health: 70, Cost: []building.Cost{{Resource: "coins", Amount: 300}, {Resource: "wood", Amount: 4}}}, {Level: 2, BuildDuration: 210 * time.Second, Population: 1, Health: 110, Cost: []building.Cost{{Resource: "coins", Amount: 1800}, {Resource: "wood", Amount: 16}, {Resource: "flax", Amount: 3}}}, {Level: 3, BuildDuration: 1205 * time.Second, Population: 1, Health: 170, Cost: []building.Cost{{Resource: "coins", Amount: 6950}, {Resource: "wood", Amount: 40}, {Resource: "flax", Amount: 10}, {Resource: "planks", Amount: 5}}}, {Level: 4, BuildDuration: 2810 * time.Second, Population: 1, Health: 250, Cost: []building.Cost{{Resource: "coins", Amount: 31000}, {Resource: "flax", Amount: 20}, {Resource: "windleaf", Amount: 3}, {Resource: "planks", Amount: 13}}}, {Level: 5, BuildDuration: 5660 * time.Second, Population: 1, Health: 360, Cost: []building.Cost{{Resource: "coins", Amount: 92400}, {Resource: "windleaf", Amount: 7}, {Resource: "planks", Amount: 34}, {Resource: "rope", Amount: 5}}}, {Level: 6, BuildDuration: 8760 * time.Second, Population: 1, Health: 500, Cost: []building.Cost{{Resource: "coins", Amount: 143200}, {Resource: "planks", Amount: 67}, {Resource: "stone", Amount: 19}, {Resource: "rope", Amount: 14}, {Resource: "windleaf", Amount: 9}}}, {Level: 7, BuildDuration: 8760 * time.Second, Population: 1, Health: 680, Cost: []building.Cost{{Resource: "coins", Amount: 230500}, {Resource: "planks", Amount: 130}, {Resource: "stone", Amount: 40}, {Resource: "rope", Amount: 26}, {Resource: "fabric", Amount: 15}}}, {Level: 8, BuildDuration: 12660 * time.Second, Population: 1, Health: 900, Cost: []building.Cost{{Resource: "coins", Amount: 361000}, {Resource: "premium_planks", Amount: 1}, {Resource: "stone_block", Amount: 18}, {Resource: "rope", Amount: 49}, {Resource: "fabric", Amount: 32}}}, {Level: 9, BuildDuration: 18780 * time.Second, Population: 1, Health: 1150, Cost: []building.Cost{{Resource: "coins", Amount: 565000}, {Resource: "premium_planks", Amount: 2}, {Resource: "stone_block", Amount: 30}, {Resource: "fabric", Amount: 57}, {Resource: "iron_ingot", Amount: 2}}}, {Level: 10, BuildDuration: 28260 * time.Second, Population: 1, Health: 1450, Cost: []building.Cost{{Resource: "coins", Amount: 817400}, {Resource: "premium_planks", Amount: 4}, {Resource: "stone_block", Amount: 61}, {Resource: "iron_ingot", Amount: 5}}}, {Level: 11, BuildDuration: 37500 * time.Second, Population: 1, Health: 1800, Cost: []building.Cost{{Resource: "coins", Amount: 1185000}, {Resource: "premium_planks", Amount: 7}, {Resource: "iron_ingot", Amount: 9}, {Resource: "gold_ingot", Amount: 2}, {Resource: "emerald_dust", Amount: 1}}}}},
	building.TypeLumberYard:     {Type: building.TypeLumberYard, Name: "Лесопильный двор", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 140 * time.Second, Population: 3, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 120}}},
	building.TypeStoneCutters:   {Type: building.TypeStoneCutters, Name: "Каменотесы", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 160 * time.Second, Population: 3, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "coins", Amount: 140}, {Resource: "wood", Amount: 60}}},
	building.TypeOilRefinery:    {Type: building.TypeOilRefinery, Name: "Нефтеперерабатывающий завод", Level: 1, Footprint: building.Footprint{Width: 1, Height: 1}, BuildDuration: 270 * time.Second, Population: 4, RequiresTownHall: true, CountsTowardLimit: true, Cost: []building.Cost{{Resource: "brick", Amount: 80}, {Resource: "metal", Amount: 30}}},
}

func GetBuilding(t building.Type) (BuildingType, bool) {
	item, ok := Buildings[t]
	return item, ok
}

func FirstLevelBuildings() []BuildingType {
	types := []building.Type{
		building.TypeTownHall,
		building.TypeDugout,
		building.TypeFieldBed,
		building.TypeWarehouse,
		building.TypeCoinStorage,
		building.TypeWorkshop,
		building.TypeMarket,
		building.TypeTower,
		building.TypeWoodenWall,
		building.TypeRoad,
		building.TypeAllianceHouse,
		building.TypeLumberYard,
		building.TypeStoneCutters,
		building.TypeOilRefinery,
	}
	items := make([]BuildingType, 0, len(types))
	for _, t := range types {
		items = append(items, Buildings[t])
	}
	return items
}
