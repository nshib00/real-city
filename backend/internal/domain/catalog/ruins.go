package catalog

import (
	"time"

	"real-city/backend/internal/domain/building"
)

// RuinSpecs describes restoration costs and durations for the twelve world ruins.
var RuinSpecs = map[building.Type]BuildingType{
	"ruins_town_square":       ruinSpec("ruins_town_square", "Старая ратушная площадь", 20*time.Hour, 1000, 300),
	"ruins_archive":           ruinSpec("ruins_archive", "Архив чертежей", 22*time.Hour, 1400, 320),
	"ruins_storage":           ruinSpec("ruins_storage", "Старый складской узел", 24*time.Hour, 1800, 350),
	"ruins_greenhouse":        ruinSpec("ruins_greenhouse", "Заросшая оранжерея", 26*time.Hour, 2400, 370),
	"ruins_water_station":     ruinSpec("ruins_water_station", "Водяная станция", 28*time.Hour, 3000, 400),
	"ruins_mechanic_workshop": ruinSpec("ruins_mechanic_workshop", "Мастерская механизмов", 30*time.Hour, 3800, 450),
	"ruins_mint":              ruinSpec("ruins_mint", "Монетный двор", 32*time.Hour, 4600, 480),
	"ruins_wind_shrine":       ruinSpec("ruins_wind_shrine", "Святилище ветра", 34*time.Hour, 5400, 510),
	"ruins_ore_obelisk":       ruinSpec("ruins_ore_obelisk", "Залежный обелиск", 36*time.Hour, 6300, 550),
	"ruins_bastion":           ruinSpec("ruins_bastion", "Каменный бастион", 40*time.Hour, 7800, 650),
	"ruins_rift_watch":        ruinSpec("ruins_rift_watch", "Разломная сторожевая", 44*time.Hour, 9400, 700),
	"ruins_river_lighthouse":  ruinSpec("ruins_river_lighthouse", "Речной маяк", 48*time.Hour, 12000, 750),
}

func ruinSpec(kind building.Type, name string, duration time.Duration, coins, health int) BuildingType {
	return BuildingType{
		Type: kind, Category: "ruins", Name: name, Level: 1,
		Footprint:     building.Footprint{Width: 1, Height: 1},
		BuildDuration: duration, Health: health, CountsTowardLimit: true,
		Cost: []building.Cost{{Resource: "coins", Amount: coins}},
	}
}

func IsRuin(kind building.Type) bool {
	_, ok := RuinSpecs[kind]
	return ok
}
