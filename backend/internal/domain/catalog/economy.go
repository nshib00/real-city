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
	{Type: economy.ResourceWindleaf, Name: "Ветролист", Category: "raw"},
	{Type: economy.ResourceHerbs, Name: "Травы", Category: "raw"},
	{Type: economy.ResourceMushrooms, Name: "Грибы", Category: "raw"},
	{Type: economy.ResourceSeeds, Name: "Семена", Category: "raw"},
	{Type: economy.ResourceBrick, Name: "Кирпич", Category: "crafted"},
	{Type: economy.ResourceStoneBlock, Name: "Каменный блок", Category: "crafted"},
	{Type: economy.ResourceMetal, Name: "Металл", Category: "crafted"},
	{Type: economy.ResourceIron, Name: "Железо", Category: "crafted"},
	{Type: economy.ResourceSteel, Name: "Сталь", Category: "crafted"},
	{Type: economy.ResourceGlass, Name: "Стекло", Category: "crafted"},
	{Type: economy.ResourcePlanks, Name: "Доски", Category: "crafted"},
	{Type: economy.ResourceCement, Name: "Цемент", Category: "crafted"},
	{Type: economy.ResourceConcrete, Name: "Бетон", Category: "crafted"},
	{Type: economy.ResourceFabric, Name: "Ткань", Category: "crafted"},
	{Type: economy.ResourceElectronics, Name: "Электроника", Category: "crafted"},
	{Type: economy.ResourceSulfur, Name: "Сера", Category: "crafted"},
	{Type: economy.ResourceExplosives, Name: "Взрывчатка", Category: "crafted"},
	{Type: economy.ResourceOil, Name: "Нефть", Category: "fuel"},
	{Type: economy.ResourceFuel, Name: "Бензин", Category: "fuel"},
	{Type: economy.ResourceSuperSeeds, Name: "Супер-семена", Category: "rare"},
	{Type: economy.ResourceSuperFiber, Name: "Супер-волокно", Category: "rare"},
	{Type: economy.ResourceSuperMushrooms, Name: "Супер-грибы", Category: "rare"},
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
}

func RecipeByID(id string) (economy.ProductionRecipe, bool) {
	for _, recipe := range ProductionRecipes {
		if recipe.ID == id {
			return recipe, true
		}
	}
	return economy.ProductionRecipe{}, false
}
