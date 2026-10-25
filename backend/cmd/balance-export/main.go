// Command balance-export captures the current runtime values as a versioned snapshot.
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
)

func main() {
	levels := make(map[string][]economy.ProductionRecipe)
	for _, base := range catalog.ProductionCatalog() {
		for level := 1; level <= 20; level++ {
			recipe, ok := catalog.RecipeForBuildingLevel(base.ID, level)
			if !ok {
				panic("missing recipe: " + base.ID)
			}
			levels[base.ID] = append(levels[base.ID], recipe)
		}
	}
	defense := make(map[string][]catalog.DefenseWeaponStats)
	for _, kind := range []building.Type{building.TypeDefenseCannon, building.TypeDefenseBoltThrower, building.TypeDefenseStormCoil} {
		for level := 1; level <= 20; level++ {
			stats, ok := catalog.DefenseWeaponLevel(kind, level)
			if !ok {
				break
			}
			defense[string(kind)] = append(defense[string(kind)], stats)
		}
	}
	cannons := make([]catalog.CannonStats, 0)
	for level := 1; level <= 20; level++ {
		stats, ok := catalog.CannonLevel(level)
		if !ok {
			break
		}
		cannons = append(cannons, stats)
	}
	payload := struct {
		SchemaVersion  int                                     `json:"schema_version"`
		BalanceVersion int                                     `json:"balance_version"`
		Resources      []catalog.ResourceSpec                  `json:"resources"`
		Recipes        []economy.ProductionRecipe              `json:"recipes"`
		RecipeLevels   map[string][]economy.ProductionRecipe   `json:"recipe_levels"`
		Monsters       []monster.Spec                          `json:"monsters"`
		Weapons        []catalog.PlayerWeaponSpec              `json:"weapons"`
		PvP            catalog.PvPRules                        `json:"pvp"`
		DefenseWeapons map[string][]catalog.DefenseWeaponStats `json:"defense_weapons"`
		Cannons        []catalog.CannonStats                   `json:"cannons"`
		Ruins          map[building.Type]catalog.BuildingType  `json:"ruins"`
	}{1, catalog.BalanceVersion, catalog.Resources, catalog.ProductionCatalog(), levels, catalog.MonsterSpecs(), catalog.PlayerWeapons, catalog.RaidRules(), defense, cannons, catalog.RuinSpecs}
	data, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		panic(err)
	}
	if _, err := fmt.Fprintln(os.Stdout, string(data)); err != nil {
		panic(err)
	}
}
