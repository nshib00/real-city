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
	BaseReward     []ResourceAmount
	CoinReward     int
	SuperChanceBps int
	SuperReward    []ResourceAmount
	Growth         []FieldStage
}

func WindleafCrop() FieldCrop {
	return FieldCrop{
		ID:             "windleaf",
		Name:           "Ветролист",
		CoinReward:     24,
		SuperChanceBps: 75,
		BaseReward:     []ResourceAmount{{Resource: ResourceWindleaf, Amount: 3}},
		SuperReward:    []ResourceAmount{{Resource: ResourceWindleaf, Amount: 9}, {Resource: ResourceSuperFiber, Amount: 1}},
		Growth: []FieldStage{
			{Index: 1, Name: "посадка", Duration: 45 * time.Second},
			{Index: 2, Name: "ранний рост", Duration: 90 * time.Second},
			{Index: 3, Name: "средний рост", Duration: 2 * time.Minute},
			{Index: 4, Name: "поздний рост", Duration: 3 * time.Minute},
			{Index: 5, Name: "готовый урожай", Ready: true},
		},
	}
}
