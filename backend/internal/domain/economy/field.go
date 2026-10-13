package economy

import "time"

type FieldStage struct {
	Index      int
	Name       string
	Duration   time.Duration
	Ready      bool
	SuperModel bool
}

type FieldCrop struct {
	ID              string
	Name            string
	Level           int
	BaseReward      []ResourceAmount
	CoinReward      int
	SuperCoinReward int
	SuperChanceBps  int
	SuperReward     []ResourceAmount
	Growth          []FieldStage
}

type fieldCropLevel struct {
	Coins              int
	Reward             []ResourceAmount
	GrowthDuration     time.Duration
	StageCount         int
	SuperChanceBps     int
	SuperCoins         int
	SuperReward        []ResourceAmount
	SuperStageDuration time.Duration
	SuperStageCount    int
}

func WindleafCrop() FieldCrop {
	return WindleafCropForLevel(1)
}

func WindleafCropForLevel(level int) FieldCrop {
	crop, _ := FieldCropForBuildingType("field_bed", level, false)
	return crop
}

func WindleafStage(crop FieldCrop, stage int) (FieldStage, bool) {
	return FieldStageByIndex(crop, stage)
}

func FieldStageByIndex(crop FieldCrop, stage int) (FieldStage, bool) {
	if stage < 1 || stage > len(crop.Growth) {
		return FieldStage{}, false
	}
	return crop.Growth[stage-1], true
}

func FieldCropForBuildingType(buildingType string, level int, super bool) (FieldCrop, bool) {
	def, ok := fieldCropCatalog[buildingType]
	if !ok {
		return FieldCrop{}, false
	}
	if level < 1 {
		level = 1
	}
	if level > len(def.Levels) {
		level = len(def.Levels)
	}
	spec := def.Levels[level-1]
	crop := FieldCrop{
		ID:              def.ID,
		Name:            def.Name,
		Level:           level,
		CoinReward:      spec.Coins,
		SuperCoinReward: spec.SuperCoins,
		SuperChanceBps:  spec.SuperChanceBps,
		BaseReward:      cloneResourceAmounts(spec.Reward),
		SuperReward:     cloneResourceAmounts(spec.SuperReward),
	}
	stageCount := spec.StageCount
	stageDuration := spec.GrowthDuration / time.Duration(stageCount)
	if super && spec.SuperStageCount > 0 && spec.SuperStageDuration > 0 {
		stageCount = spec.SuperStageCount
		stageDuration = spec.SuperStageDuration
	}
	crop.Growth = make([]FieldStage, 0, stageCount)
	if crop.SuperCoinReward <= 0 {
		crop.SuperCoinReward = crop.CoinReward
	}
	for i := 1; i <= stageCount; i++ {
		crop.Growth = append(crop.Growth, FieldStage{
			Index:      i,
			Name:       def.StageNames[min(i, len(def.StageNames))-1],
			Duration:   stageDuration,
			Ready:      i == stageCount,
			SuperModel: super,
		})
	}
	return crop, true
}

func IsFieldCropBuildingType(buildingType string) bool {
	_, ok := fieldCropCatalog[buildingType]
	return ok
}

func cloneResourceAmounts(items []ResourceAmount) []ResourceAmount {
	result := make([]ResourceAmount, len(items))
	copy(result, items)
	return result
}

type fieldCropDefinition struct {
	ID         string
	Name       string
	StageNames []string
	Levels     []fieldCropLevel
}

var fieldCropCatalog = map[string]fieldCropDefinition{
	"field_bed": {
		ID:         "windleaf",
		Name:       "Ветролист",
		StageNames: []string{"маленькие зеленые росточки", "небольшие листья", "крупные листья с жилками", "готовые высокие листья", "супер-рост", "готовый супер-урожай"},
		Levels: []fieldCropLevel{
			{Coins: 190, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 1}}, GrowthDuration: 135 * time.Second, StageCount: 4},
			{Coins: 900, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 1}}, GrowthDuration: 190 * time.Second, StageCount: 4},
			{Coins: 2400, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 2}}, GrowthDuration: 450 * time.Second, StageCount: 4, SuperChanceBps: 10, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 787*time.Second + 500*time.Millisecond, SuperStageCount: 6},
			{Coins: 8300, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 2}}, GrowthDuration: 530 * time.Second, StageCount: 4, SuperChanceBps: 15, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 927*time.Second + 500*time.Millisecond, SuperStageCount: 6},
			{Coins: 15000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 3}}, GrowthDuration: 565 * time.Second, StageCount: 4, SuperChanceBps: 20, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 988*time.Second + 750*time.Millisecond, SuperStageCount: 6},
			{Coins: 23000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 4}}, GrowthDuration: 610 * time.Second, StageCount: 4, SuperChanceBps: 27, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1067*time.Second + 500*time.Millisecond, SuperStageCount: 6},
			{Coins: 34000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 5}}, GrowthDuration: 635 * time.Second, StageCount: 4, SuperChanceBps: 35, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1111*time.Second + 250*time.Millisecond, SuperStageCount: 6},
			{Coins: 48500, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 6}}, GrowthDuration: 660 * time.Second, StageCount: 4, SuperChanceBps: 45, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1155 * time.Second, SuperStageCount: 6},
			{Coins: 59000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 7}}, GrowthDuration: 710 * time.Second, StageCount: 4, SuperChanceBps: 55, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1242*time.Second + 500*time.Millisecond, SuperStageCount: 6},
			{Coins: 72000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 9}}, GrowthDuration: 760 * time.Second, StageCount: 4, SuperChanceBps: 65, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1330 * time.Second, SuperStageCount: 6},
			{Coins: 86000, Reward: []ResourceAmount{{Resource: ResourceWindleaf, Amount: 11}}, GrowthDuration: 825 * time.Second, StageCount: 4, SuperChanceBps: 75, SuperReward: []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}}, SuperStageDuration: 1443*time.Second + 750*time.Millisecond, SuperStageCount: 6},
		},
	},
	"seed_garden": {
		ID:         "seeds",
		Name:       "Семена",
		StageNames: []string{"посев и метки посадки", "рост семенных коробочек", "готовые семенные лотки", "редкие семенные коробочки", "крупные редкие корзинки", "готовый супер-урожай"},
		Levels: []fieldCropLevel{
			{Coins: 50, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 5}}, GrowthDuration: 570 * time.Second, StageCount: 3},
			{Coins: 280, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 10}}, GrowthDuration: 780 * time.Second, StageCount: 3},
			{Coins: 760, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 14}}, GrowthDuration: 915 * time.Second, StageCount: 3, SuperChanceBps: 20, SuperCoins: 8500, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 25}, {Resource: ResourceSuperSeeds, Amount: 1}}, SuperStageDuration: 1280 * time.Second, SuperStageCount: 6},
			{Coins: 1500, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 18}}, GrowthDuration: 990 * time.Second, StageCount: 3, SuperChanceBps: 25, SuperCoins: 16500, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 36}, {Resource: ResourceSuperSeeds, Amount: 1}}, SuperStageDuration: 1385 * time.Second, SuperStageCount: 6},
			{Coins: 2600, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 23}}, GrowthDuration: 1065 * time.Second, StageCount: 3, SuperChanceBps: 32, SuperCoins: 28600, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 46}, {Resource: ResourceSuperSeeds, Amount: 1}}, SuperStageDuration: 1490 * time.Second, SuperStageCount: 6},
			{Coins: 4100, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 29}}, GrowthDuration: 1110 * time.Second, StageCount: 3, SuperChanceBps: 40, SuperCoins: 45100, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 58}, {Resource: ResourceSuperSeeds, Amount: 1}}, SuperStageDuration: 1555 * time.Second, SuperStageCount: 6},
			{Coins: 6300, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 36}}, GrowthDuration: 1160 * time.Second, StageCount: 3, SuperChanceBps: 50, SuperCoins: 69300, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 72}, {Resource: ResourceSuperSeeds, Amount: 1}}, SuperStageDuration: 1625 * time.Second, SuperStageCount: 6},
			{Coins: 9300, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 45}}, GrowthDuration: 1215 * time.Second, StageCount: 3, SuperChanceBps: 62, SuperCoins: 102300, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 90}, {Resource: ResourceSuperSeeds, Amount: 2}}, SuperStageDuration: 1700 * time.Second, SuperStageCount: 6},
			{Coins: 13200, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 56}}, GrowthDuration: 1270 * time.Second, StageCount: 3, SuperChanceBps: 75, SuperCoins: 145200, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 112}, {Resource: ResourceSuperSeeds, Amount: 2}}, SuperStageDuration: 1780 * time.Second, SuperStageCount: 6},
			{Coins: 18000, Reward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 70}}, GrowthDuration: 1350 * time.Second, StageCount: 3, SuperChanceBps: 90, SuperCoins: 198000, SuperReward: []ResourceAmount{{Resource: ResourceSeeds, Amount: 140}, {Resource: ResourceSuperSeeds, Amount: 2}}, SuperStageDuration: 1890 * time.Second, SuperStageCount: 6},
		},
	},
	"flax_field": {
		ID:         "flax",
		Name:       "Лен",
		StageNames: []string{"тонкие ростки льна", "стебли с голубыми цветками", "готовые пучки льна", "редкие густые стебли", "качественное волокно", "готовый редкий лен"},
		Levels: []fieldCropLevel{
			{Coins: 100, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 7}}, GrowthDuration: 480 * time.Second, StageCount: 3},
			{Coins: 340, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 12}}, GrowthDuration: 720 * time.Second, StageCount: 3},
			{Coins: 860, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 18}}, GrowthDuration: 900 * time.Second, StageCount: 3, SuperChanceBps: 15, SuperCoins: 3450, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 42}, {Resource: ResourceSuperFiber, Amount: 1}}, SuperStageDuration: 1080 * time.Second, SuperStageCount: 6},
			{Coins: 1450, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 26}}, GrowthDuration: 1020 * time.Second, StageCount: 3, SuperChanceBps: 20, SuperCoins: 5800, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 62}, {Resource: ResourceSuperFiber, Amount: 1}}, SuperStageDuration: 1225 * time.Second, SuperStageCount: 6},
			{Coins: 2250, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 36}}, GrowthDuration: 1140 * time.Second, StageCount: 3, SuperChanceBps: 28, SuperCoins: 9000, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 84}, {Resource: ResourceSuperFiber, Amount: 1}}, SuperStageDuration: 1370 * time.Second, SuperStageCount: 6},
			{Coins: 3350, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 49}}, GrowthDuration: 1260 * time.Second, StageCount: 3, SuperChanceBps: 36, SuperCoins: 13400, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 115}, {Resource: ResourceSuperFiber, Amount: 1}}, SuperStageDuration: 1515 * time.Second, SuperStageCount: 6},
			{Coins: 4900, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 65}}, GrowthDuration: 1380 * time.Second, StageCount: 3, SuperChanceBps: 45, SuperCoins: 19600, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 152}, {Resource: ResourceSuperFiber, Amount: 1}}, SuperStageDuration: 1660 * time.Second, SuperStageCount: 6},
			{Coins: 7000, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 84}}, GrowthDuration: 1500 * time.Second, StageCount: 3, SuperChanceBps: 58, SuperCoins: 28000, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 196}, {Resource: ResourceSuperFiber, Amount: 2}}, SuperStageDuration: 1800 * time.Second, SuperStageCount: 6},
			{Coins: 9600, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 106}}, GrowthDuration: 1620 * time.Second, StageCount: 3, SuperChanceBps: 72, SuperCoins: 38400, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 248}, {Resource: ResourceSuperFiber, Amount: 2}}, SuperStageDuration: 1950 * time.Second, SuperStageCount: 6},
			{Coins: 12800, Reward: []ResourceAmount{{Resource: ResourceFlax, Amount: 132}}, GrowthDuration: 1800 * time.Second, StageCount: 3, SuperChanceBps: 85, SuperCoins: 51200, SuperReward: []ResourceAmount{{Resource: ResourceFlax, Amount: 310}, {Resource: ResourceSuperFiber, Amount: 2}}, SuperStageDuration: 2160 * time.Second, SuperStageCount: 6},
		},
	},
	"herb_bed": {
		ID:         "herbs",
		Name:       "Травы",
		StageNames: []string{"редкие травяные ростки", "низкая аптекарская зелень", "плотные травяные кустики", "готовая цветущая трава", "редкие аптекарские цветы", "готовый редкий травяной урожай"},
		Levels:     fieldLevels(ResourceHerbs, []int{1200, 2200, 3600, 5600, 8200, 11600, 15800, 21000, 27500}, []int{8, 12, 17, 23, 30, 38, 48, 60, 75}, []time.Duration{16 * time.Minute, 17 * time.Minute, 18 * time.Minute, 20 * time.Minute, 22 * time.Minute, 24 * time.Minute, 26 * time.Minute, 28 * time.Minute, 30 * time.Minute}, []int{0, 0, 20, 25, 32, 40, 50, 62, 75}, ResourceRareFlowers, []int{0, 0, 1, 1, 1, 1, 2, 2, 3}),
	},
	"mushroom_grove": {
		ID:         "mushrooms",
		Name:       "Грибы",
		StageNames: []string{"влажная почва и бугорки", "маленькие шляпки", "группы средних грибов", "готовая грибница", "крупные супер-грибы", "готовый редкий грибной урожай"},
		Levels:     fieldLevels(ResourceMushrooms, []int{650, 1300, 2300, 3900, 6200, 9300, 13200, 18500, 25200, 34000}, []int{6, 10, 15, 21, 29, 38, 49, 62, 78, 96}, []time.Duration{14 * time.Minute, 15 * time.Minute, 16 * time.Minute, 18 * time.Minute, 20 * time.Minute, 22 * time.Minute, 24 * time.Minute, 27 * time.Minute, 30 * time.Minute, 32 * time.Minute}, []int{0, 0, 18, 22, 28, 35, 45, 58, 72, 90}, ResourceSuperMushrooms, []int{0, 0, 1, 1, 1, 1, 2, 2, 2, 3}),
	},
	"reed_bed": {
		ID:         "reed",
		Name:       "Тростник",
		StageNames: []string{"короткие зеленые иглы", "низкие пучки тростника", "высокие стебли с метелками", "готовый плотный тростник", "редкие крепкие стебли", "готовый редкий тростник"},
		Levels:     fieldLevels(ResourceReed, []int{420, 820, 1500, 2600, 4300, 6800, 10200, 14800, 21000, 29200}, []int{7, 11, 16, 23, 31, 41, 53, 67, 84, 104}, []time.Duration{12 * time.Minute, 13 * time.Minute, 14 * time.Minute, 16 * time.Minute, 18 * time.Minute, 20 * time.Minute, 22 * time.Minute, 24 * time.Minute, 25 * time.Minute, 26 * time.Minute}, []int{0, 0, 15, 20, 26, 34, 44, 56, 70, 85}, ResourceSuperFiber, []int{0, 0, 1, 1, 1, 1, 1, 2, 2, 2}),
	},
	"dye_garden": {
		ID:         "dyes",
		Name:       "Красители",
		StageNames: []string{"посаженные пигментные ростки", "цветные низкие пятна", "плотные красильные культуры", "готовые пигментные лотки", "редкие цветочные пигменты", "готовый редкий красильный урожай"},
		Levels:     fieldLevels(ResourceDyes, []int{18500, 31000, 49000, 73500, 106000, 150000}, []int{18, 28, 42, 60, 82, 110}, []time.Duration{35 * time.Minute, 39 * time.Minute, 44 * time.Minute, 49 * time.Minute, 55 * time.Minute, 60 * time.Minute}, []int{35, 45, 58, 72, 88, 105}, ResourceRareFlowers, []int{1, 1, 2, 2, 3, 4}),
	},
	"oilseed_field": {
		ID:         "oil_plants",
		Name:       "Масличные растения",
		StageNames: []string{"зеленые ростки", "кусты с желтыми бутонами", "семенные головки", "готовые корзины семян", "редкие масличные головки", "готовый редкий масличный урожай"},
		Levels:     fieldLevels(ResourceOilPlants, []int{7600, 12200, 18800, 27800, 39800, 55500, 76000}, []int{14, 22, 33, 47, 64, 86, 112}, []time.Duration{22 * time.Minute, 24 * time.Minute, 26 * time.Minute, 28 * time.Minute, 30 * time.Minute, 32 * time.Minute, 34 * time.Minute}, []int{20, 28, 38, 50, 64, 80, 100}, ResourceSuperSeeds, []int{1, 1, 1, 1, 2, 2, 3}),
	},
	"sugar_bed": {
		ID:         "sugar_cane",
		Name:       "Сахарный тростник",
		StageNames: []string{"короткие толстые ростки", "стебли до середины борта", "плотные перевязанные стебли", "готовая сахарная культура", "редкие сладкие стебли", "готовый редкий сахарный урожай"},
		Levels:     fieldLevels(ResourceSugarCane, []int{4200, 7200, 11800, 18000, 26500, 38000, 53000, 72000, 96000}, []int{10, 16, 24, 34, 47, 63, 82, 105, 132}, []time.Duration{18 * time.Minute, 20 * time.Minute, 22 * time.Minute, 24 * time.Minute, 26 * time.Minute, 28 * time.Minute, 30 * time.Minute, 32 * time.Minute, 34 * time.Minute}, []int{0, 0, 18, 24, 32, 42, 54, 68, 85}, ResourceSuperSeeds, []int{0, 0, 1, 1, 1, 1, 2, 2, 3}),
	},
	"crystal_greenhouse": {
		ID:         "crystal_fruit",
		Name:       "Кристальные плоды",
		StageNames: []string{"маленький кристальный росток", "светлые стебли", "кристальные листья и первые плоды", "готовые светящиеся плоды", "редкие кристальные плоды", "готовый редкий кристальный урожай"},
		Levels:     fieldLevels(ResourceCrystalFruit, []int{85000, 140000, 215000, 320000}, []int{3, 5, 8, 12}, []time.Duration{90 * time.Minute, 110 * time.Minute, 130 * time.Minute, 150 * time.Minute}, []int{45, 65, 85, 110}, ResourceAeolianCrystal, []int{1, 1, 1, 2}),
	},
}

func fieldLevels(resource ResourceType, coins []int, amounts []int, growth []time.Duration, chances []int, superResource ResourceType, superAmounts []int) []fieldCropLevel {
	levels := make([]fieldCropLevel, 0, len(coins))
	for index := range coins {
		level := fieldCropLevel{
			Coins:          coins[index],
			Reward:         []ResourceAmount{{Resource: resource, Amount: amounts[index]}},
			GrowthDuration: growth[index],
			StageCount:     4,
			SuperChanceBps: chances[index],
		}
		if chances[index] > 0 && superAmounts[index] > 0 {
			level.SuperCoins = coins[index] * 4
			level.SuperReward = []ResourceAmount{{Resource: resource, Amount: amounts[index] * 3}, {Resource: superResource, Amount: superAmounts[index]}}
			level.SuperStageDuration = growth[index] * 2
			level.SuperStageCount = 6
		}
		levels = append(levels, level)
	}
	return levels
}
