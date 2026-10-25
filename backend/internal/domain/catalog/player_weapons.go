package catalog

import (
	"time"

	"real-city/backend/internal/domain/economy"
)

type PlayerWeaponSpec struct {
	Resource       economy.ResourceType
	Name           string
	Damage         int
	ColossusDamage int
	Range          int
	Fuse           time.Duration
}

var PlayerWeapons = []PlayerWeaponSpec{
	{economy.ResourceThrowingKnives, "Метательные клинки", 80, 40, 2, 0},
	{economy.ResourceHuntingTraps, "Охотничий капкан", 100, 100, 1, 15 * time.Second},
	{economy.ResourceBlackpowderBomb, "Пороховая бомба", 220, 220, 2, 40 * time.Second},
	{economy.ResourceFirebomb, "Огненная бомба", 225, 225, 2, 2 * time.Minute},
	{economy.ResourceShapedCharge, "Направленный заряд", 140, 140, 1, 5 * time.Minute},
	{economy.ResourceShockCharge, "Импульсный заряд", 700, 700, 3, 15 * time.Minute},
	{economy.ResourceSiegeMine, "Осадная мина", 500, 500, 1, 20 * time.Minute},
	{economy.ResourceBreachBomb, "Проломная бомба", 400, 400, 1, 30 * time.Minute},
	{economy.ResourceResonanceCharge, "Резонансный заряд", 2500, 7500, 2, 45 * time.Minute},
}

func PlayerWeaponByResource(resource economy.ResourceType) (PlayerWeaponSpec, bool) {
	for _, item := range PlayerWeapons {
		if item.Resource == resource {
			return item, true
		}
	}
	return PlayerWeaponSpec{}, false
}

func init() {
	ProductionRecipes = append(ProductionRecipes,
		weaponRecipe("throwing_knives_batch", "Метательные клинки", "forge", 1, 8, 3, economy.ResourceThrowingKnives, 6, []economy.ResourceAmount{{economy.ResourceIronIngot, 3}, {economy.ResourceWood, 3}, {economy.ResourceCoal, 2}}),
		weaponRecipe("hunting_traps_batch", "Охотничьи капканы", "workshop", 1, 12, 3, economy.ResourceHuntingTraps, 3, []economy.ResourceAmount{{economy.ResourcePlanks, 6}, {economy.ResourceRope, 3}, {economy.ResourceIronIngot, 2}}),
		weaponRecipe("blackpowder_bomb_batch", "Пороховые бомбы", "workshop", 1, 16, 4, economy.ResourceBlackpowderBomb, 4, []economy.ResourceAmount{{economy.ResourceSulfur, 4}, {economy.ResourceCoal, 5}, {economy.ResourceClay, 4}, {economy.ResourcePaper, 2}}),
		weaponRecipe("shaped_charge_batch", "Направленные заряды", "military_factory", 1, 25, 7, economy.ResourceShapedCharge, 2, []economy.ResourceAmount{{economy.ResourceExplosives, 2}, {economy.ResourceSteel, 3}, {economy.ResourceFabric, 2}}),
		weaponRecipe("firebomb_batch", "Огненные бомбы", "chemical_workshop", 1, 20, 5, economy.ResourceFirebomb, 4, []economy.ResourceAmount{{economy.ResourceFuel, 4}, {economy.ResourceResin, 3}, {economy.ResourceFabric, 2}, {economy.ResourceGlass, 2}}),
		weaponRecipe("shock_charge_batch", "Импульсные заряды", "electronics_workshop", 1, 30, 7, economy.ResourceShockCharge, 2, []economy.ResourceAmount{{economy.ResourceElectronics, 2}, {economy.ResourceCopperParts, 3}, {economy.ResourceGlass, 2}, {economy.ResourceFuel, 2}}),
		weaponRecipe("siege_mine_batch", "Осадные мины", "siege_yard", 1, 40, 8, economy.ResourceSiegeMine, 2, []economy.ResourceAmount{{economy.ResourceExplosives, 3}, {economy.ResourceSteel, 4}, {economy.ResourceMechanism, 1}, {economy.ResourceRope, 2}}),
		weaponRecipe("breach_bomb_batch", "Проломные бомбы", "siege_yard", 2, 55, 10, economy.ResourceBreachBomb, 2, []economy.ResourceAmount{{economy.ResourceExplosives, 5}, {economy.ResourceSteel, 5}, {economy.ResourceArmorPlates, 2}, {economy.ResourceFuel, 3}}),
		weaponRecipe("resonance_charge_batch", "Резонансные заряды", "resonance_laboratory", 1, 60, 12, economy.ResourceResonanceCharge, 2, []economy.ResourceAmount{{economy.ResourceExplosives, 4}, {economy.ResourceElectronics, 3}, {economy.ResourceMechanism, 2}, {economy.ResourceSteel, 3}}),
	)
}

func weaponRecipe(id, name, building string, level, minutes, workers int, output economy.ResourceType, amount int, input []economy.ResourceAmount) economy.ProductionRecipe {
	return economy.ProductionRecipe{ID: id, Name: name, BuildingType: building, RequiredLevel: level, Duration: time.Duration(minutes) * time.Minute, Workers: workers, Input: input, Output: []economy.ResourceAmount{{Resource: output, Amount: amount}}}
}
