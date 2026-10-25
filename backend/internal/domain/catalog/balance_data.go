package catalog

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"real-city/backend/internal/domain/building"
)

//go:embed buildings.v2.json
var buildingBalanceJSON []byte

var buildingBalanceOnce sync.Once
var firstLevelTypes []building.Type
var directPlacement = make(map[building.Type]bool)

type balanceCost struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}
type balanceLevel struct {
	Level        int           `json:"level"`
	BuildSeconds int           `json:"buildSeconds"`
	Population   int           `json:"population"`
	Health       int           `json:"health"`
	Cost         []balanceCost `json:"cost"`
	NextType     string        `json:"nextType"`
}
type balanceBuilding struct {
	Type      string `json:"type"`
	Category  string `json:"category"`
	Name      string `json:"name"`
	Level     int    `json:"level"`
	Footprint struct {
		Width  int `json:"width"`
		Height int `json:"height"`
	} `json:"footprint"`
	BuildSeconds  int            `json:"buildSeconds"`
	Population    int            `json:"population"`
	Health        int            `json:"health"`
	Cost          []balanceCost  `json:"cost"`
	UpgradeTo     []string       `json:"upgradeTo"`
	FirstLevel    bool           `json:"firstLevel"`
	UpgradeLevels []balanceLevel `json:"upgradeLevels"`
}

func balanceCosts(costs []balanceCost) []building.Cost {
	result := make([]building.Cost, 0, len(costs))
	for _, cost := range costs {
		result = append(result, building.Cost{Resource: cost.Resource, Amount: cost.Amount})
	}
	return result
}

// applyBuildingBalance makes the versioned data authoritative for runtime balance.
// Existing Go definitions retain rule flags and act as a compatibility manifest.
func applyBuildingBalance() {
	var payload struct {
		SchemaVersion  int               `json:"schema_version"`
		BalanceVersion int               `json:"balance_version"`
		Buildings      []balanceBuilding `json:"buildings"`
	}
	if err := json.Unmarshal(buildingBalanceJSON, &payload); err != nil {
		panic(err)
	}
	if payload.SchemaVersion != 1 || payload.BalanceVersion != BalanceVersion {
		panic("unsupported building balance version")
	}
	if len(payload.Buildings) != len(Buildings) {
		panic(fmt.Sprintf("building balance count %d does not match runtime %d", len(payload.Buildings), len(Buildings)))
	}
	seen := make(map[string]bool, len(payload.Buildings))
	for _, entry := range payload.Buildings {
		if seen[entry.Type] {
			panic("duplicate building balance ID: " + entry.Type)
		}
		seen[entry.Type] = true
		spec, ok := Buildings[building.Type(entry.Type)]
		if !ok {
			panic("unknown building balance ID: " + entry.Type)
		}
		if entry.Footprint.Width < 1 || entry.Footprint.Height < 1 || entry.BuildSeconds < 0 || entry.Population < 0 || entry.Health <= 0 {
			panic("invalid building balance: " + entry.Type)
		}
		spec.Name = entry.Name
		spec.Category = entry.Category
		spec.Level = entry.Level
		spec.Footprint = building.Footprint{Width: entry.Footprint.Width, Height: entry.Footprint.Height}
		spec.BuildDuration = time.Duration(entry.BuildSeconds) * time.Second
		spec.Population = entry.Population
		spec.Health = entry.Health
		spec.Cost = balanceCosts(entry.Cost)
		spec.UpgradeTo = make([]building.Type, 0, len(entry.UpgradeTo))
		for _, next := range entry.UpgradeTo {
			spec.UpgradeTo = append(spec.UpgradeTo, building.Type(next))
		}
		spec.UpgradeLevels = make([]BuildingUpgradeLevel, 0, len(entry.UpgradeLevels))
		for _, level := range entry.UpgradeLevels {
			if level.Level < 1 || level.BuildSeconds < 0 || level.Population < 0 || level.Health <= 0 {
				panic("invalid building level: " + entry.Type)
			}
			spec.UpgradeLevels = append(spec.UpgradeLevels, BuildingUpgradeLevel{
				Level: level.Level, BuildDuration: time.Duration(level.BuildSeconds) * time.Second,
				Population: level.Population, Health: level.Health, Cost: balanceCosts(level.Cost), NextType: building.Type(level.NextType),
			})
		}
		Buildings[building.Type(entry.Type)] = spec
		if entry.FirstLevel {
			firstLevelTypes = append(firstLevelTypes, building.Type(entry.Type))
		}
		directPlacement[building.Type(entry.Type)] = entry.FirstLevel
	}
}

func ensureBuildingBalance() { buildingBalanceOnce.Do(applyBuildingBalance) }

func CanPlaceDirectly(t building.Type) bool {
	ensureBuildingBalance()
	return directPlacement[t]
}
