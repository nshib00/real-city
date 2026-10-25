package main

import (
	"encoding/json"
	"os"
	"sort"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
)

type level struct {
	Level        int            `json:"level"`
	BuildSeconds int            `json:"buildSeconds"`
	Population   int            `json:"population"`
	Health       int            `json:"health"`
	Cost         map[string]int `json:"cost"`
}

func costs(items []building.Cost) map[string]int {
	result := make(map[string]int, len(items))
	for _, item := range items {
		result[item.Resource] = item.Amount
	}
	return result
}

func main() {
	keys := make([]string, 0, len(catalog.Buildings))
	for key := range catalog.Buildings {
		keys = append(keys, string(key))
	}
	sort.Strings(keys)
	result := make(map[string]any, len(keys))
	for _, key := range keys {
		item, ok := catalog.GetBuilding(building.Type(key))
		if !ok {
			panic("missing catalog item: " + key)
		}
		levels := make([]level, 0, len(item.UpgradeLevels))
		for _, upgrade := range item.UpgradeLevels {
			levels = append(levels, level{Level: upgrade.Level, BuildSeconds: int(upgrade.BuildDuration.Seconds()), Population: upgrade.Population, Health: upgrade.Health, Cost: costs(upgrade.Cost)})
		}
		if len(levels) == 0 {
			levels = append(levels, level{Level: item.Level, BuildSeconds: int(item.BuildDuration.Seconds()), Population: item.Population, Health: item.Health, Cost: costs(item.Cost)})
		}
		upgrades := make([]string, 0, len(item.UpgradeTo))
		for _, next := range item.UpgradeTo {
			upgrades = append(upgrades, string(next))
		}
		result[key] = map[string]any{
			"name": item.Name, "category": item.Category,
			"footprint": map[string]int{"width": item.Footprint.Width, "height": item.Footprint.Height},
			"upgradeTo": upgrades, "levels": levels,
		}
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		panic(err)
	}
}
