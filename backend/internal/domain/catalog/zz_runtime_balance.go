package catalog

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
)

//go:embed balance.v2.json
var runtimeBalanceJSON []byte

var recipeLevels map[string][]economy.ProductionRecipe
var activePvPRules PvPRules
var activeDefenseWeapons map[string][]DefenseWeaponStats
var activeCannons []CannonStats

type PvPRules struct {
	RaidTravelSeconds   int `json:"raid_travel_seconds"`
	RaidDamage          int `json:"raid_damage"`
	RaidRangeTiles      int `json:"raid_range_tiles"`
	RaidCooldownSeconds int `json:"raid_cooldown_seconds"`
}

func RaidRules() PvPRules { return activePvPRules }

type runtimeBalance struct {
	SchemaVersion  int                                   `json:"schema_version"`
	BalanceVersion int                                   `json:"balance_version"`
	Resources      []ResourceSpec                        `json:"resources"`
	Recipes        []economy.ProductionRecipe            `json:"recipes"`
	RecipeLevels   map[string][]economy.ProductionRecipe `json:"recipe_levels"`
	Monsters       []monster.Spec                        `json:"monsters"`
	Weapons        []PlayerWeaponSpec                    `json:"weapons"`
	PvP            PvPRules                              `json:"pvp"`
	DefenseWeapons map[string][]DefenseWeaponStats       `json:"defense_weapons"`
	Cannons        []CannonStats                         `json:"cannons"`
	Ruins          map[building.Type]BuildingType        `json:"ruins"`
}

func decodeRuntimeBalance(data []byte) (runtimeBalance, error) {
	var snapshot runtimeBalance
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&snapshot); err != nil {
		return snapshot, err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return snapshot, fmt.Errorf("unexpected trailing balance data: %v", err)
	}
	if snapshot.SchemaVersion != 1 || snapshot.BalanceVersion != BalanceVersion {
		return snapshot, fmt.Errorf("unsupported runtime balance version: %d/%d", snapshot.SchemaVersion, snapshot.BalanceVersion)
	}
	if len(snapshot.Resources) == 0 || len(snapshot.Recipes) == 0 || len(snapshot.Monsters) == 0 || len(snapshot.Weapons) == 0 {
		return snapshot, fmt.Errorf("incomplete runtime balance")
	}
	if snapshot.PvP.RaidTravelSeconds <= 0 || snapshot.PvP.RaidDamage <= 0 || snapshot.PvP.RaidRangeTiles <= 0 || snapshot.PvP.RaidCooldownSeconds <= 0 {
		return snapshot, fmt.Errorf("invalid PvP rules")
	}
	if len(snapshot.Cannons) == 0 || len(snapshot.DefenseWeapons) != 3 {
		return snapshot, fmt.Errorf("incomplete defense balance")
	}
	if len(snapshot.Ruins) != len(RuinSpecs) {
		return snapshot, fmt.Errorf("incomplete ruin balance")
	}
	resources := make(map[economy.ResourceType]bool)
	for _, item := range snapshot.Resources {
		if item.Type == "" || item.Name == "" || resources[item.Type] {
			return snapshot, fmt.Errorf("invalid or duplicate resource: %s", item.Type)
		}
		resources[item.Type] = true
	}
	recipes := make(map[string]bool)
	validateRecipe := func(item economy.ProductionRecipe) error {
		if item.ID == "" || item.Name == "" || item.BuildingType == "" || item.Duration <= 0 || item.Workers < 0 || item.FuelPerRun < 0 || len(item.Output) == 0 {
			return fmt.Errorf("invalid recipe: %s", item.ID)
		}
		for _, amount := range append(append([]economy.ResourceAmount{}, item.Input...), item.Output...) {
			if !resources[amount.Resource] || amount.Amount <= 0 {
				return fmt.Errorf("invalid resource in recipe %s: %s", item.ID, amount.Resource)
			}
		}
		for _, rare := range item.RareOutput {
			if !resources[rare.Resource] || rare.Amount <= 0 || rare.Chance <= 0 || rare.Chance > 1 {
				return fmt.Errorf("invalid rare output in recipe: %s", item.ID)
			}
		}
		return nil
	}
	for _, item := range snapshot.Recipes {
		if recipes[item.ID] {
			return snapshot, fmt.Errorf("duplicate recipe: %s", item.ID)
		}
		recipes[item.ID] = true
		if err := validateRecipe(item); err != nil {
			return snapshot, err
		}
		levels := snapshot.RecipeLevels[item.ID]
		if len(levels) != 20 {
			return snapshot, fmt.Errorf("recipe %s needs 20 level snapshots", item.ID)
		}
		for _, level := range levels {
			if level.ID != item.ID {
				return snapshot, fmt.Errorf("level recipe ID mismatch: %s", item.ID)
			}
			if err := validateRecipe(level); err != nil {
				return snapshot, err
			}
		}
	}
	if len(snapshot.RecipeLevels) != len(recipes) {
		return snapshot, fmt.Errorf("orphan recipe levels")
	}
	monsterTypes := make(map[monster.Type]bool)
	for _, item := range snapshot.Monsters {
		if item.Type == "" || item.Name == "" || item.MaxHealth <= 0 || item.Damage <= 0 || item.AttackCooldown <= 0 || item.SpawnWeight <= 0 || monsterTypes[item.Type] {
			return snapshot, fmt.Errorf("invalid or duplicate monster: %s", item.Type)
		}
		monsterTypes[item.Type] = true
	}
	weapons := make(map[economy.ResourceType]bool)
	for _, item := range snapshot.Weapons {
		if !resources[item.Resource] || item.Name == "" || item.Damage <= 0 || item.Range <= 0 || item.Fuse < 0 || weapons[item.Resource] {
			return snapshot, fmt.Errorf("invalid or duplicate weapon: %s", item.Resource)
		}
		weapons[item.Resource] = true
	}
	for _, item := range snapshot.Cannons {
		if item.Range <= 0 || item.Damage <= 0 || !resources[item.Ammo] {
			return snapshot, fmt.Errorf("invalid cannon stats")
		}
	}
	for _, kind := range []string{"defense_cannon", "defense_bolt_thrower", "defense_storm_coil"} {
		levels := snapshot.DefenseWeapons[kind]
		if len(levels) == 0 {
			return snapshot, fmt.Errorf("missing defense balance: %s", kind)
		}
		for _, item := range levels {
			if item.Range <= 0 || item.Damage <= 0 || item.Cooldown <= 0 || item.DamageType == "" || item.Ammo != "" && !resources[item.Ammo] {
				return snapshot, fmt.Errorf("invalid defense stats: %s", kind)
			}
		}
	}
	for kind, item := range snapshot.Ruins {
		if item.Type != kind || item.Name == "" || item.Category != "ruins" || item.Footprint.Width != 1 || item.Footprint.Height != 1 || item.Health <= 0 || item.BuildDuration < 20*time.Hour || item.BuildDuration > 48*time.Hour {
			return snapshot, fmt.Errorf("invalid ruin balance: %s", kind)
		}
		for _, cost := range item.Cost {
			if !resources[economy.ResourceType(cost.Resource)] || cost.Amount <= 0 {
				return snapshot, fmt.Errorf("invalid ruin cost: %s", kind)
			}
		}
	}
	return snapshot, nil
}

func init() {
	snapshot, err := decodeRuntimeBalance(runtimeBalanceJSON)
	if err != nil {
		panic(err)
	}
	Resources = snapshot.Resources
	ProductionRecipes = snapshot.Recipes
	recipeLevels = snapshot.RecipeLevels
	monsterSpecs = snapshot.Monsters
	PlayerWeapons = snapshot.Weapons
	activePvPRules = snapshot.PvP
	activeDefenseWeapons = snapshot.DefenseWeapons
	activeCannons = snapshot.Cannons
	RuinSpecs = snapshot.Ruins
}
