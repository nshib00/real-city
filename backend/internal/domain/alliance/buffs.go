package alliance

import (
	"embed"
	"encoding/json"
)

//go:embed buffs.json
var buffData embed.FS

type BuffDefinition struct {
	ID       BuffID `json:"id"`
	Name     string `json:"name"`
	Effect   string `json:"effect"`
	Percent  int    `json:"percent"`
	MaxLevel int    `json:"max_level"`
	Resource string `json:"resource"`
	BaseCost int    `json:"base_cost"`
}

var BuffCatalog = func() []BuffDefinition {
	raw, err := buffData.ReadFile("buffs.json")
	if err != nil {
		panic(err)
	}
	var defs []BuffDefinition
	if err = json.Unmarshal(raw, &defs); err != nil {
		panic(err)
	}
	return defs
}()

func BuffSpec(id BuffID) (BuffDefinition, bool) {
	for _, v := range BuffCatalog {
		if v.ID == id {
			return v, true
		}
	}
	return BuffDefinition{}, false
}
