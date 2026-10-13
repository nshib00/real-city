package catalog

import (
	"time"

	"real-city/backend/internal/domain/economy"
)

type ResourceSpec struct {
	Type        economy.ResourceType
	Name        string
	Category    string
	HasLimit    bool
	Description string
}

var Resources = []ResourceSpec{
	{Type: economy.ResourceCoins, Name: "Монеты", Category: "basic", HasLimit: true, Description: "Базовая валюта, лимит задают хранилища монет."},
	{Type: economy.ResourcePopulation, Name: "Жители", Category: "basic", Description: "Рабочая сила для стройки, полей, заводов и ремонта."},
	{Type: economy.ResourceAeolianCrystal, Name: "Эолийские кристаллы", Category: "basic", Description: "Премиумный ресурс: тонкие вытянутые шестиугольные аметистовые кристаллы."},
	{Type: economy.ResourceWood, Name: "Древесина", Category: "raw"},
	{Type: economy.ResourceStone, Name: "Камень", Category: "raw"},
	{Type: economy.ResourceClay, Name: "Глина", Category: "raw"},
	{Type: economy.ResourceSand, Name: "Песок", Category: "raw"},
	{Type: economy.ResourceCoal, Name: "Уголь", Category: "raw"},
	{Type: economy.ResourceIronOre, Name: "Железная руда", Category: "raw"},
	{Type: economy.ResourceCopper, Name: "Медь", Category: "raw"},
	{Type: economy.ResourceResin, Name: "Смола", Category: "raw"},
	{Type: economy.ResourceFlax, Name: "Лен", Category: "raw"},
	{Type: economy.ResourceReed, Name: "Тростник", Category: "raw"},
	{Type: economy.ResourceWindleaf, Name: "Ветролист", Category: "raw"},
	{Type: economy.ResourceHerbs, Name: "Травы", Category: "raw"},
	{Type: economy.ResourceMushrooms, Name: "Грибы", Category: "raw"},
	{Type: economy.ResourceSeeds, Name: "Семена", Category: "raw"},
	{Type: economy.ResourceDyes, Name: "Красители", Category: "raw"},
	{Type: economy.ResourceOilPlants, Name: "Масличные растения", Category: "raw"},
	{Type: economy.ResourceSugarCane, Name: "Сахарный тростник", Category: "raw"},
	{Type: economy.ResourceCrystalFruit, Name: "Кристальные плоды", Category: "rare"},
	{Type: economy.ResourceBrick, Name: "Кирпич", Category: "crafted"},
	{Type: economy.ResourceStoneBlock, Name: "Каменный блок", Category: "crafted"},
	{Type: economy.ResourceMetal, Name: "Металл", Category: "crafted"},
	{Type: economy.ResourceIron, Name: "Железо", Category: "crafted"},
	{Type: economy.ResourceSteel, Name: "Сталь", Category: "crafted"},
	{Type: economy.ResourceGlass, Name: "Стекло", Category: "crafted"},
	{Type: economy.ResourceStarGlass, Name: "Звездное стекло", Category: "rare", Description: "Редкая стеклянная заготовка из точных стекольных циклов."},
	{Type: economy.ResourceLightCrystal, Name: "Светокристалл", Category: "rare", Description: "Сверхредкий прозрачный кристалл для поздней оптики и усилений."},
	{Type: economy.ResourcePlanks, Name: "Доски", Category: "crafted"},
	{Type: economy.ResourcePremiumPlanks, Name: "Премиум-доски", Category: "crafted"},
	{Type: economy.ResourceRope, Name: "Веревка", Category: "crafted"},
	{Type: economy.ResourceTools, Name: "Инструменты", Category: "crafted"},
	{Type: economy.ResourceIronIngot, Name: "Железный слиток", Category: "crafted"},
	{Type: economy.ResourceGoldIngot, Name: "Золотой слиток", Category: "crafted"},
	{Type: economy.ResourceCement, Name: "Цемент", Category: "crafted"},
	{Type: economy.ResourceConcrete, Name: "Бетон", Category: "crafted"},
	{Type: economy.ResourceReinforcedConc, Name: "Железобетон", Category: "crafted"},
	{Type: economy.ResourceReinforcedBeam, Name: "Усиленные балки", Category: "crafted"},
	{Type: economy.ResourceArmorPlates, Name: "Защитные пластины", Category: "crafted"},
	{Type: economy.ResourceFabric, Name: "Ткань", Category: "crafted"},
	{Type: economy.ResourceElectronics, Name: "Электроника", Category: "crafted"},
	{Type: economy.ResourceSulfur, Name: "Сера", Category: "crafted"},
	{Type: economy.ResourceExplosives, Name: "Взрывчатка", Category: "crafted"},
	{Type: economy.ResourceOil, Name: "Нефть", Category: "fuel"},
	{Type: economy.ResourceFuel, Name: "Бензин", Category: "fuel"},
	{Type: economy.ResourceSuperSeeds, Name: "Супер-семена", Category: "rare"},
	{Type: economy.ResourceSuperFiber, Name: "Супер-волокно", Category: "rare"},
	{Type: economy.ResourceSuperMushrooms, Name: "Супер-грибы", Category: "rare"},
	{Type: economy.ResourceSuperWindleaf, Name: "Супер-ветролист", Category: "rare"},
	{Type: economy.ResourceEmeraldDust, Name: "Изумрудная пыль", Category: "rare"},
	{Type: economy.ResourceRareFlowers, Name: "Редкие цветы", Category: "rare"},
	{Type: economy.ResourceElderwoodHeart, Name: "Сердцевина древня", Category: "rare", Description: "Редкая находка при рубке леса."},
	{Type: economy.ResourceRuneTile, Name: "Руническая черепица", Category: "rare"},
	{Type: economy.ResourceBlueSalt, Name: "Синяя соль", Category: "rare", Description: "Редкая минеральная примесь из песчаных карьеров."},
}

func ResourceByType(t economy.ResourceType) (ResourceSpec, bool) {
	for _, resource := range Resources {
		if resource.Type == t {
			return resource, true
		}
	}
	return ResourceSpec{}, false
}

var ProductionRecipes = []economy.ProductionRecipe{
	{
		ID:           "planks_from_wood",
		Name:         "Распил древесины",
		BuildingType: "lumber_yard",
		Duration:     2 * time.Minute,
		Workers:      2,
		Input:        []economy.ResourceAmount{{Resource: economy.ResourceWood, Amount: 12}},
		Output:       []economy.ResourceAmount{{Resource: economy.ResourcePlanks, Amount: 6}},
	},
	{
		ID:           "stone_blocks",
		Name:         "Каменные блоки",
		BuildingType: "stone_cutters",
		Duration:     3 * time.Minute,
		Workers:      2,
		Input:        []economy.ResourceAmount{{Resource: economy.ResourceStone, Amount: 16}},
		Output:       []economy.ResourceAmount{{Resource: economy.ResourceStoneBlock, Amount: 4}},
	},
	{
		ID:           "brick_batch",
		Name:         "Обжиг кирпича",
		BuildingType: "workshop",
		Duration:     4 * time.Minute,
		Workers:      3,
		Input:        []economy.ResourceAmount{{Resource: economy.ResourceClay, Amount: 12}, {Resource: economy.ResourceCoal, Amount: 4}},
		Output:       []economy.ResourceAmount{{Resource: economy.ResourceBrick, Amount: 10}},
	},
	{
		ID:           "fuel_from_oil",
		Name:         "Переработка бензина",
		BuildingType: "oil_refinery",
		Duration:     6 * time.Minute,
		Workers:      4,
		Input:        []economy.ResourceAmount{{Resource: economy.ResourceOil, Amount: 8}},
		Output:       []economy.ResourceAmount{{Resource: economy.ResourceFuel, Amount: 5}},
	},
	{
		ID:           "sand_quarry_run",
		Name:         "Добыча песка",
		BuildingType: "sand_quarry",
		Duration:     530 * time.Second,
		Workers:      4,
		Output:       []economy.ResourceAmount{{Resource: economy.ResourceSand, Amount: 10}, {Resource: economy.ResourceCoins, Amount: 70}},
	},
	{
		ID:           "glass_batch",
		Name:         "Плавка стекла",
		BuildingType: "glass_workshop",
		Duration:     800 * time.Second,
		Workers:      6,
		Input:        []economy.ResourceAmount{{Resource: economy.ResourceSand, Amount: 28}, {Resource: economy.ResourceCoal, Amount: 1}},
		Output:       []economy.ResourceAmount{{Resource: economy.ResourceGlass, Amount: 1}},
	},
}

func RecipeByID(id string) (economy.ProductionRecipe, bool) {
	for _, recipe := range ProductionRecipes {
		if recipe.ID == id {
			return recipe, true
		}
	}
	return economy.ProductionRecipe{}, false
}

func RecipeForBuildingLevel(id string, level int) (economy.ProductionRecipe, bool) {
	recipe, ok := RecipeByID(id)
	if !ok {
		return economy.ProductionRecipe{}, false
	}
	if id == "sand_quarry_run" {
		if level < 1 {
			level = 1
		}
		if level > len(sandQuarryRecipes) {
			level = len(sandQuarryRecipes)
		}
		spec := sandQuarryRecipes[level-1]
		recipe.Duration = spec.Duration
		recipe.Workers = spec.Workers
		recipe.RequiredLevel = level
		recipe.Input = nil
		recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourceSand, Amount: spec.Sand}, {Resource: economy.ResourceCoins, Amount: spec.Coins}}
		if spec.BlueSaltChance > 0 {
			recipe.RareOutput = []economy.RareProductionOutput{{Resource: economy.ResourceBlueSalt, Amount: 1, Chance: spec.BlueSaltChance}}
		}
		return recipe, true
	}
	if id == "glass_batch" {
		if level < 1 {
			level = 1
		}
		if level > len(glassWorkshopRecipes) {
			level = len(glassWorkshopRecipes)
		}
		spec := glassWorkshopRecipes[level-1]
		recipe.Duration = spec.Duration
		recipe.Workers = spec.Workers
		recipe.RequiredLevel = level
		recipe.Input = []economy.ResourceAmount{{Resource: economy.ResourceSand, Amount: spec.Sand}}
		if spec.Coal > 0 {
			recipe.Input = append(recipe.Input, economy.ResourceAmount{Resource: economy.ResourceCoal, Amount: spec.Coal})
		}
		recipe.FuelPerRun = spec.Fuel
		recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourceGlass, Amount: spec.Glass}}
		if spec.StarGlassChance > 0 {
			recipe.RareOutput = append(recipe.RareOutput, economy.RareProductionOutput{Resource: economy.ResourceStarGlass, Amount: 1, Chance: spec.StarGlassChance})
		}
		if spec.LightCrystalChance > 0 {
			recipe.RareOutput = append(recipe.RareOutput, economy.RareProductionOutput{Resource: economy.ResourceLightCrystal, Amount: 1, Chance: spec.LightCrystalChance})
		}
		return recipe, true
	}
	if id != "planks_from_wood" {
		return recipe, true
	}
	if level < 1 {
		level = 1
	}
	if level > len(lumberYardRecipes) {
		level = len(lumberYardRecipes)
	}
	spec := lumberYardRecipes[level-1]
	recipe.Duration = spec.Duration
	recipe.Workers = spec.Workers
	recipe.RequiredLevel = level
	recipe.Input = []economy.ResourceAmount{{Resource: economy.ResourceWood, Amount: spec.Wood}}
	if spec.Fuel > 0 {
		recipe.FuelPerRun = spec.Fuel
	}
	recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourcePlanks, Amount: spec.Planks}}
	return recipe, true
}

type lumberYardRecipe struct {
	Wood     int
	Planks   int
	Fuel     int
	Workers  int
	Duration time.Duration
}

var lumberYardRecipes = []lumberYardRecipe{
	{Wood: 15, Planks: 2, Workers: 3, Duration: 270 * time.Second},
	{Wood: 13, Planks: 4, Workers: 3, Duration: 490 * time.Second},
	{Wood: 19, Planks: 7, Workers: 4, Duration: 765 * time.Second},
	{Wood: 24, Planks: 11, Fuel: 5, Workers: 4, Duration: 1395 * time.Second},
	{Wood: 30, Planks: 15, Fuel: 8, Workers: 5, Duration: 1770 * time.Second},
	{Wood: 35, Planks: 20, Fuel: 13, Workers: 5, Duration: 2040 * time.Second},
	{Wood: 40, Planks: 25, Fuel: 17, Workers: 6, Duration: 2230 * time.Second},
	{Wood: 44, Planks: 33, Fuel: 20, Workers: 6, Duration: 2420 * time.Second},
	{Wood: 50, Planks: 37, Fuel: 25, Workers: 7, Duration: 2575 * time.Second},
	{Wood: 53, Planks: 40, Fuel: 34, Workers: 7, Duration: 2700 * time.Second},
	{Wood: 55, Planks: 44, Fuel: 40, Workers: 8, Duration: 2855 * time.Second},
	{Wood: 58, Planks: 54, Fuel: 47, Workers: 8, Duration: 3100 * time.Second},
	{Wood: 65, Planks: 65, Fuel: 55, Workers: 9, Duration: 3185 * time.Second},
}

type sandQuarryRecipe struct {
	Sand           int
	Coins          int
	Workers        int
	Duration       time.Duration
	BlueSaltChance float64
}

var sandQuarryRecipes = []sandQuarryRecipe{
	{Sand: 10, Coins: 70, Workers: 4, Duration: 530 * time.Second},
	{Sand: 17, Coins: 110, Workers: 5, Duration: 460 * time.Second},
	{Sand: 26, Coins: 240, Workers: 7, Duration: 615 * time.Second, BlueSaltChance: 0.012},
	{Sand: 34, Coins: 450, Workers: 8, Duration: 890 * time.Second, BlueSaltChance: 0.025},
	{Sand: 41, Coins: 1020, Workers: 10, Duration: 1055 * time.Second, BlueSaltChance: 0.039},
	{Sand: 53, Coins: 1650, Workers: 12, Duration: 1200 * time.Second, BlueSaltChance: 0.057},
	{Sand: 65, Coins: 2600, Workers: 15, Duration: 1350 * time.Second, BlueSaltChance: 0.08},
	{Sand: 81, Coins: 5950, Workers: 17, Duration: 1610 * time.Second, BlueSaltChance: 0.101},
	{Sand: 93, Coins: 9000, Workers: 19, Duration: 2055 * time.Second, BlueSaltChance: 0.127},
	{Sand: 102, Coins: 14300, Workers: 21, Duration: 2325 * time.Second, BlueSaltChance: 0.15},
	{Sand: 114, Coins: 19300, Workers: 23, Duration: 2810 * time.Second, BlueSaltChance: 0.174},
}

type glassWorkshopRecipe struct {
	Sand               int
	Coal               int
	Fuel               int
	Glass              int
	Workers            int
	Duration           time.Duration
	StarGlassChance    float64
	LightCrystalChance float64
}

var glassWorkshopRecipes = []glassWorkshopRecipe{
	{Sand: 28, Coal: 1, Glass: 1, Workers: 6, Duration: 800 * time.Second},
	{Sand: 40, Coal: 1, Glass: 2, Workers: 8, Duration: 1040 * time.Second},
	{Sand: 33, Coal: 1, Glass: 2, Workers: 9, Duration: 760 * time.Second, StarGlassChance: 0.004},
	{Sand: 47, Coal: 2, Glass: 3, Workers: 11, Duration: 1235 * time.Second, StarGlassChance: 0.0065},
	{Sand: 40, Coal: 2, Glass: 3, Workers: 13, Duration: 1060 * time.Second, StarGlassChance: 0.008, LightCrystalChance: 0.0001},
	{Sand: 54, Fuel: 12, Glass: 4, Workers: 16, Duration: 1530 * time.Second, StarGlassChance: 0.01, LightCrystalChance: 0.0003},
	{Sand: 64, Fuel: 15, Glass: 5, Workers: 19, Duration: 1875 * time.Second, StarGlassChance: 0.0125, LightCrystalChance: 0.0006},
	{Sand: 75, Fuel: 21, Glass: 6, Workers: 22, Duration: 2360 * time.Second, StarGlassChance: 0.0145, LightCrystalChance: 0.001},
	{Sand: 87, Fuel: 26, Glass: 7, Workers: 24, Duration: 2700 * time.Second, StarGlassChance: 0.016, LightCrystalChance: 0.0015},
}
