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
	ID             string
	Name           string
	Level          int
	BaseReward     []ResourceAmount
	CoinReward     int
	SuperChanceBps int
	SuperReward    []ResourceAmount
	Growth         []FieldStage
}

func WindleafCrop() FieldCrop {
	return WindleafCropForLevel(1)
}

func WindleafCropForLevel(level int) FieldCrop {
	if level < 1 {
		level = 1
	}
	if level > len(windleafCropLevels) {
		level = len(windleafCropLevels)
	}
	spec := windleafCropLevels[level-1]
	stageDuration := spec.GrowthDuration / 4
	return FieldCrop{
		ID:             "windleaf",
		Name:           "Ветролист",
		Level:          level,
		CoinReward:     spec.Coins,
		SuperChanceBps: spec.SuperChanceBps,
		BaseReward:     []ResourceAmount{{Resource: ResourceWindleaf, Amount: spec.Windleaf}},
		SuperReward:    []ResourceAmount{{Resource: ResourceSuperWindleaf, Amount: 1}},
		Growth: []FieldStage{
			{Index: 1, Name: "маленькие зеленые росточки", Duration: stageDuration},
			{Index: 2, Name: "небольшие листья", Duration: stageDuration},
			{Index: 3, Name: "крупные листья с жилками", Duration: stageDuration},
			{Index: 4, Name: "готовые высокие листья", Duration: stageDuration, Ready: true},
		},
	}
}

type windleafCropLevel struct {
	Coins          int
	Windleaf       int
	GrowthDuration time.Duration
	SuperChanceBps int
}

var windleafCropLevels = []windleafCropLevel{
	{Coins: 190, Windleaf: 1, GrowthDuration: 135 * time.Second},
	{Coins: 900, Windleaf: 1, GrowthDuration: 190 * time.Second},
	{Coins: 2400, Windleaf: 2, GrowthDuration: 450 * time.Second, SuperChanceBps: 10},
	{Coins: 8300, Windleaf: 2, GrowthDuration: 530 * time.Second, SuperChanceBps: 15},
	{Coins: 15000, Windleaf: 3, GrowthDuration: 565 * time.Second, SuperChanceBps: 20},
	{Coins: 23000, Windleaf: 4, GrowthDuration: 610 * time.Second, SuperChanceBps: 27},
	{Coins: 34000, Windleaf: 5, GrowthDuration: 635 * time.Second, SuperChanceBps: 35},
	{Coins: 48500, Windleaf: 6, GrowthDuration: 660 * time.Second, SuperChanceBps: 45},
	{Coins: 59000, Windleaf: 7, GrowthDuration: 710 * time.Second, SuperChanceBps: 55},
	{Coins: 72000, Windleaf: 9, GrowthDuration: 760 * time.Second, SuperChanceBps: 65},
	{Coins: 86000, Windleaf: 11, GrowthDuration: 825 * time.Second, SuperChanceBps: 75},
}
